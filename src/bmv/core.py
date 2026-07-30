import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# 配置模块日志记录器
logger = logging.getLogger(__name__)

# 变换器接口类型：接收旧文件名，返回新文件名
Transformer = Callable[[str], str]


@dataclass
class RenameAction:
    original_path: Path
    target_path: Path


class Pipeline:
    """顺序管道：按照添加顺序依次对文件名执行变换操作"""

    def __init__(self):
        self._transformers: list[Transformer] = []

    def add_transformer(self, transformer: Transformer) -> "Pipeline":
        self._transformers.append(transformer)
        return self

    def apply(self, filename: str) -> str:
        """顺次穿过所有变换节点"""
        name, ext = os.path.splitext(filename)
        for transformer in self._transformers:
            name = transformer(name)
        return f"{name}{ext}"


# --- 常用内置变换器工厂 ---

def make_delete_transformer(words: list[str]) -> Transformer:
    def _transform(name: str) -> str:
        for word in words:
            name = name.replace(word, "")
        return name
    return _transform


def make_replace_transformer(old: str, new: str) -> Transformer:
    def _transform(name: str) -> str:
        return name.replace(old, new)
    return _transform


def make_affix_transformer(prefix: str = "", suffix: str = "") -> Transformer:
    def _transform(name: str) -> str:
        return f"{prefix}{name}{suffix}"
    return _transform


def make_case_transformer(mode: str) -> Transformer:
    def _transform(name: str) -> str:
        if mode == "upper":
            return name.upper()
        elif mode == "lower":
            return name.lower()
        elif mode == "title":
            return name.title()
        return name
    return _transform


# --- 事务与撤销管理器 ---

class Transaction:
    """事务对象：负责安全校验与原子执行"""

    def __init__(self, actions: list[RenameAction]):
        self.actions = [a for a in actions if a.original_path != a.target_path]

    def validate(self) -> list[str]:
        """严格的前置安全校验，确保写入 100% 安全"""
        errors = []
        seen_targets = set()
        source_paths = {a.original_path for a in self.actions}

        for action in self.actions:
            # 1. 源文件是否存在
            if not action.original_path.exists():
                errors.append(f"源文件不存在: {action.original_path.name}")

            # 2. 目标路径内部冲突（本次修改中是否有两个文件改成了同一个名字）
            if action.target_path in seen_targets:
                errors.append(f"命名冲突，多个文件将重命名为同一名字: {action.target_path.name}")
            seen_targets.add(action.target_path)

            # 3. 与磁盘上已有文件的冲突
            if action.target_path.exists() and action.target_path not in source_paths:
                errors.append(f"目标文件名已存在于磁盘中: {action.target_path.name}")

        return errors

    def execute(self) -> tuple[int, list[str]]:
        """执行改名操作并返回成功数量与错误信息"""
        executed_actions: list[RenameAction] = []
        errors = []

        for action in self.actions:
            try:
                action.original_path.rename(action.target_path)
                executed_actions.append(action)
            except OSError as e:
                # 记录精细的系统错误日志
                msg = f"重命名失败 ({action.original_path.name} -> {action.target_path.name}): {e.strerror or e}"
                logger.error(msg)
                errors.append(msg)

                # 触发局部保护性回滚，并收集回滚错误
                rollback_errors = self._rollback(executed_actions)
                errors.extend(rollback_errors)
                return 0, errors

        # 写入撤销历史记录
        try:
            UndoJournal.save_journal(executed_actions)
        except OSError as e:
            logger.warning("修改成功，但写入 Undo 日志失败: %s", e)

        return len(executed_actions), []

    def _rollback(self, actions: list[RenameAction]) -> list[str]:
        """回滚已执行的重命名动作（不再静默忽略异常，而是记录日志与错误）"""
        rollback_errors = []
        for action in reversed(actions):
            try:
                action.target_path.rename(action.original_path)
            except OSError as e:
                err_msg = f"中途回滚失败，无法将 {action.target_path.name} 还原为 {action.original_path.name}: {e.strerror or e}"
                logger.critical(err_msg)
                rollback_errors.append(err_msg)

        return rollback_errors


class UndoJournal:
    """持久化历史记录，提供撤销功能"""

    JOURNAL_FILE = Path.home() / ".config" / "bmv" / "last_history.json"

    @classmethod
    def save_journal(cls, actions: list[RenameAction]):
        cls.JOURNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "original": str(a.original_path.resolve()),
                "target": str(a.target_path.resolve()),
            }
            for a in actions
        ]
        with open(cls.JOURNAL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def undo_last(cls) -> tuple[int, list[str]]:
        if not cls.JOURNAL_FILE.exists():
            return 0, ["没有找到可撤销的历史记录。"]

        try:
            with open(cls.JOURNAL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            err_msg = f"历史记录文件格式损坏或无法读取: {e}"
            logger.error(err_msg)
            return 0, [err_msg]

        # 🚨 关键修复 1：兼容 json 文件中单条记录 (dict) 与多条记录 (list) 的情况
        if isinstance(data, dict):
            data = [data]

        try:
            reversed_actions = [
                RenameAction(
                    original_path=Path(item["target"]),
                    target_path=Path(item["original"]),
                )
                for item in data
            ]
        except (KeyError, TypeError) as e:
            err_msg = f"历史记录数据结构异常: {e}"
            logger.error(err_msg)
            return 0, [err_msg]

        # 校验后逆向执行
        tx = Transaction(reversed_actions)
        errors = tx.validate()
        if errors:
            return 0, errors

        count, exec_errors = tx.execute()
        if count > 0:
            # 撤销成功后清除日志防止重复撤销
            try:
                cls.JOURNAL_FILE.unlink(missing_ok=True)
            except OSError as e:
                logger.warning("已成功撤销，但清理历史日志文件失败: %s", e)

        return count, exec_errors