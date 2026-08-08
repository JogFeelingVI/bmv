from pathlib import Path

from typer.testing import CliRunner

from bmv.cli import app

runner = CliRunner()


# --- 1. CLI 基础与选项校验测试 ---

def test_cli_help_option():
    """验证 CLI 根命令及子命令的 --help 参数正常输出"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "bmv" in result.stdout or "Usage" in result.stdout

    result_replace = runner.invoke(app, ["replace", "--help"])
    assert result_replace.exit_code == 0
    assert "--regex" in result_replace.stdout


def test_cli_invalid_directory_path():
    """验证传入不存在的文件夹路径时 CLI 抛出错误"""
    result = runner.invoke(app, [
        "replace",
        "-p", "/non/existent/directory/path",
        "-f", "old",
        "-r", "new"
    ])
    assert result.exit_code != 0
    assert "不存在" in result.stdout or "Invalid" in result.stdout or "Error" in result.stdout


# --- 2. replace 命令测试 (Dry-Run 与 Regex) ---

def test_cli_replace_dry_run(tmp_path: Path):
    """验证 replace 命令在 -d (--dry-run) 模式下仅生成预览，不变更磁盘文件"""
    file_a = tmp_path / "old_version.txt"
    file_a.write_text("sample content")

    result = runner.invoke(app, [
        "replace",
        "-p", str(tmp_path),
        "-f", "old",
        "-r", "new",
        "--dry-run"
    ])

    assert result.exit_code == 0
    assert "Dry-Run" in result.stdout or "预览" in result.stdout
    assert file_a.exists()  # 确保原文件未改变
    assert not (tmp_path / "new_version.txt").exists()


def test_cli_replace_regex_execution(tmp_path: Path):
    """验证 replace 命令结合正则表达式批量提取与重命名"""
    f1 = tmp_path / "img_20260807.png"
    f2 = tmp_path / "img_20260808.png"
    f1.write_text("1")
    f2.write_text("2")

    result = runner.invoke(app, [
        "replace",
        "-p", str(tmp_path),
        "-f", r"img_(\d{8})",
        "-r", r"photo_\1",
        "--regex"
    ])

    assert result.exit_code == 0
    assert (tmp_path / "photo_20260807.png").exists()
    assert (tmp_path / "photo_20260808.png").exists()
    assert not f1.exists()


# --- 3. format 命令测试 (行业预设与命名风格) ---

def test_cli_format_industry_preset(tmp_path: Path):
    """验证 format 命令解析行业预设动态参数 (--project, --scene)"""
    media_file = tmp_path / "raw_clip.mp4"
    media_file.write_text("stream")

    result = runner.invoke(app, [
        "format",
        "-p", str(tmp_path),
        "-e", "mp4",
        "-pr", "media",
        "--project", "PROJECT_A",
        "--scene", "SC01"
    ])

    assert result.exit_code == 0
    # 匹配生成的标准文件名格式 PROJECT_A_SC01_YYYYMMDD_001.mp4
    renamed_files = list(tmp_path.glob("PROJECT_A_SC01_*_001.mp4"))
    assert len(renamed_files) == 1


def test_cli_format_case_style_kebab(tmp_path: Path):
    """验证 format 命令转换为连结命名风格 (-st kebab)"""
    doc = tmp_path / "My Final Proposal.docx"
    doc.write_text("document")

    result = runner.invoke(app, [
        "format",
        "-p", str(tmp_path),
        "-st", "kebab"
    ])

    assert result.exit_code == 0
    assert (tmp_path / "my-final-proposal.docx").exists()


# --- 4. 交互式提示 (Interactive Input) 模拟测试 ---

def test_cli_confirmation_prompt_declined(tmp_path: Path):
    """验证使用 input 参数模拟终端交互拒绝 ('n') 逻辑"""
    file_a = tmp_path / "data.log"
    file_a.write_text("log data")

    # 通过 input="n\n" 模拟用户输入 No 拒绝操作
    result = runner.invoke(
        app,
        ["random", "-p", str(tmp_path), "--confirm"],
        input="n\n"
    )

    assert result.exit_code != 0 or "已取消" in result.stdout or "Aborted" in result.stdout
    assert file_a.exists()  # 文件保留原样


def test_cli_confirmation_prompt_accepted(tmp_path: Path):
    """验证使用 input 参数模拟终端交互确认 ('y') 逻辑"""
    file_a = tmp_path / "data.log"
    file_a.write_text("log data")

    # 通过 input="y\n" 模拟用户输入 Yes 确认操作
    result = runner.invoke(
        app,
        ["random", "-p", str(tmp_path), "--confirm"],
        input="y\n"
    )

    assert result.exit_code == 0
    assert not file_a.exists()  # 已被重命名为随机名


# --- 5. 重命名冲突处理测试 ---

def test_cli_conflict_prevention(tmp_path: Path):
    """验证当批量重命名操作会导致目标文件名重叠时，CLI 输出冲突警告并中止"""
    (tmp_path / "item_1.txt").write_text("a")
    (tmp_path / "item_2.txt").write_text("b")

    # 正则导致两者均尝试覆盖为同一文件名 item_same.txt
    result = runner.invoke(app, [
        "replace",
        "-p", str(tmp_path),
        "-f", r"item_\d",
        "-r", "item_same",
        "--regex"
    ])

    assert result.exit_code != 0
    assert "冲突" in result.stdout or "Error" in result.stdout