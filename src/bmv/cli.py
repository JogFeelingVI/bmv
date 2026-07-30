import glob
import os
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

try:
    from . import core
except ImportError:
    # 兼容直接使用 python ./src/bmv/cli.py 运行的情况
    import core


app = typer.Typer(
    help="bmv: 现代化、安全、基于管道链的批量文件重命名工具。",
    add_completion=False,
)
console = Console()

def resolve_targets(patterns: list[str]) -> list[Path]:
    """
    解析传入的 patterns，兼顾：
    1. Shell 展开后的具体文件列表 (例如: file1.mkv file2.mkv)
    2. 带引号未展开的 Glob 通配符 (例如: "*.mkv", "./**/*.mp4")
    3. 支持用户目录 '~' 的展开
    """
    matched_files: list[Path] = []
    seen = set()

    for pat in patterns:
        # 展平波浪号 '~'
        expanded_pat = os.path.expanduser(pat)

        # 如果包含 Glob 通配符
        if any(char in expanded_pat for char in ["*", "?", "["]):
            for p in glob.glob(expanded_pat, recursive=True):
                path = Path(p).resolve()
                if path.is_file() and path not in seen:
                    seen.add(path)
                    matched_files.append(path)
        else:
            # 普通文件路径（Shell 自动展开的情况）
            path = Path(expanded_pat).resolve()
            if path.exists() and path.is_file() and path not in seen:
                seen.add(path)
                matched_files.append(path)

    return matched_files

@app.callback(invoke_without_command=True, context_settings={"allow_interspersed_args": True})
def main(
    ctx: typer.Context,
    pattern: Annotated[
        list[str] | None,
        typer.Argument(help="目标文件匹配模式 (支持 Glob 通配符，如 './videos/*.mp4')", show_default=False),
    ] = None,
    list_files: Annotated[
        bool,
        typer.Option("--list", "-l", help="仅展示匹配到的文件列表，不执行变换与重命名"),
    ] = False,
    delete: Annotated[
        list[str] | None,
        typer.Option("--delete", "-d", help="需要删除的字符串或词组"),
    ] = None,
    replace: Annotated[
        tuple[str, str] | None,
        typer.Option("--replace", "-r", help="替换字符串，格式: 旧字符串 新字符串"),
    ] = None,
    prefix: Annotated[
        str,
        typer.Option("--prefix", "-p", help="给文件名添加的前缀"),
    ] = "",
    suffix: Annotated[
        str,
        typer.Option("--suffix", "-s", help="给文件名添加的后缀"),
    ] = "",
    case: Annotated[
        str | None,
        typer.Option("--case", "-c", help="大小写转换 (upper / lower / title)"),
    ] = None,
    save: Annotated[
        bool,
        typer.Option("--save", help="确认将修改写入磁盘 (默认仅预览)"),
    ] = False,
):
    """根据规则批量重命名文件 (默认处于安全预览模式)"""

    # 如果用户执行的是子命令（例如 bmv undo），则跳过主逻辑
    if ctx.invoked_subcommand is not None:
        return

    # 如果用户没有传入任何匹配模式，显示 Help 帮助文档
    if pattern is None:
        console.print(ctx.get_help())
        raise typer.Exit()

    # if pattern and ("--list" in pattern or "-l" in pattern):
    #     list_files = True
    #     pattern = [p for p in pattern if p not in ("--list", "-l")]
    # 🚨 3. 新增：拦截 `bmv undo` 命令，直接触发 undo 逻辑
    if pattern and pattern == ["undo"]:
        undo_cmd()
        raise typer.Exit()

    matched_paths = resolve_targets(pattern)
    # 🚨 新增拦截判断：如果没有匹配到任何文件，明确提示并退出！
    if not matched_paths:
        console.print("[bold red]❌ 未找到任何匹配的文件，请检查路径是否正确！[/bold red]")
        raise typer.Exit(code=1)

    if list_files:
        table = Table(title=f"📁 匹配的文件列表 (共 {len(matched_paths)} 个)")
        table.add_column("序号", justify="right", style="cyan", no_wrap=True)
        table.add_column("文件名", style="bold green")

        for idx, f in enumerate(matched_paths, 1):
            table.add_row(str(idx), f.name)

        console.print(table)
        raise typer.Exit()  # 打印完直接退出，不进入重命名逻辑

    # 1. 构建管道变换链
    pipeline = core.Pipeline()
    if delete:
        pipeline.add_transformer(core.make_delete_transformer(delete))
    if replace:
        pipeline.add_transformer(core.make_replace_transformer(replace[0], replace[1]))
    if case:
        pipeline.add_transformer(core.make_case_transformer(case.lower()))
    if prefix or suffix:
        pipeline.add_transformer(core.make_affix_transformer(prefix, suffix))

    # 3. 产生重命名动作列表
    actions = []
    for path in matched_paths:
        new_name = pipeline.apply(path.name)
        actions.append(core.RenameAction(original_path=path, target_path=path.with_name(new_name)))

    transaction = core.Transaction(actions)

    if not transaction.actions:
        console.print("[green]所有匹配的文件名均无需变更。[/green]")
        return

    # 4. 进行安全校验
    validation_errors = transaction.validate()
    if validation_errors:
        console.print("[bold red]安全校验失败，拒绝执行操作:[/bold red]")
        for err in validation_errors:
            console.print(f"  [red]• {err}[/red]")
        raise typer.Exit(code=1)

    # 5. 可视化表格展现
    table = Table(title=f"变更对照表 (共 {len(transaction.actions)} 个文件)", show_lines=True)
    table.add_column("源文件路径", style="cyan")
    table.add_column("目标文件名", style="green")

    for action in transaction.actions:
        table.add_row(str(action.original_path.name), action.target_path.name)

    console.print(table)

    # 6. 执行或预览
    if not save:
        console.print("\n[bold yellow]当前处于预览模式。[/bold yellow]")
        console.print("请添加 [bold green]--save[/bold green] 参数以真正应用修改。")
    else:
        success_count, errors = transaction.execute()
        if errors:
            console.print("[bold red]重命名过程中发生错误:[/bold red]")
            for err in errors:
                console.print(f"  [red]• {err}[/red]")
        else:
            console.print(f"\n[bold green]成功重命名 {success_count} 个文件！[/bold green]")
            console.print("[dim]提示: 如果发现改错，可以随时输入 [bold]bmv undo[/bold] 撤销本次操作。[/dim]")


@app.command(name="undo")
def undo_cmd():
    """一键撤销上一次的重命名操作"""
    console.print("[blue]正在尝试撤销上一次的重命名...[/blue]")
    count, errors = core.UndoJournal.undo_last()

    if errors:
        console.print("[bold red]撤销失败:[/bold red]")
        for err in errors:
            console.print(f"  [red]• {err}[/red]")
    else:
        console.print(f"[bold green]撤销成功！已恢复 {count} 个文件。[/bold green]")


if __name__ == "__main__":
    app()