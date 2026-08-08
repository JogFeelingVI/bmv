from pathlib import Path

from pytest_mock import MockerFixture
from rich.panel import Panel
from rich.table import Table
from typer.testing import CliRunner

from bmv.cli import app

runner = CliRunner()


# --- 1. 验证表格 (Rich Table) 预览渲染逻辑 ---

def test_dry_run_table_rendering(tmp_path: Path, mocker: MockerFixture):
    """使用 pytest-mock 拦截 Console.print，验证 Dry-Run 模式下是否正确构造并输出了对比表格"""
    # 模拟准备文件
    (tmp_path / "old_doc.txt").write_text("test")

    # Mock bmv.cli 中使用的 Rich Console 实例的 print 方法
    mock_console_print = mocker.patch("bmv.cli.console.print")

    result = runner.invoke(app, [
        "replace",
        "-p", str(tmp_path),
        "-f", "old",
        "-r", "new",
        "--dry-run"
    ])

    assert result.exit_code == 0
    assert mock_console_print.called

    # 从 mock_console_print 的调用历史中检索出 Table 对象
    printed_tables = [
        call.args[0] for call in mock_console_print.call_args_list 
        if call.args and isinstance(call.args[0], Table)
    ]

    assert len(printed_tables) >= 1
    table: Table = printed_tables[0]

    # 校验表格列头名称
    column_headers = [col.header for col in table.columns]
    assert "Original Name" in column_headers or "原文件名" in column_headers
    assert "New Name" in column_headers or "重命名后" in column_headers

    # 校验表格中的行数据（原文件名与新文件名）
    # Rich Table 的 raw rows 保存在 table.columns 中，可通过遍历取值
    col_old_values = [str(cell) for cell in table.columns[0].cells]
    col_new_values = [str(cell) for cell in table.columns[1].cells]

    assert any("old_doc.txt" in val for val in col_old_values)
    assert any("new_doc.txt" in val for val in col_new_values)


# --- 2. 验证警告面板 (Rich Panel) 输出 ---

def test_conflict_warning_panel(tmp_path: Path, mocker: MockerFixture):
    """验证遇到命名冲突时，是否通过 Rich Panel 输出了高亮的警告面板"""
    (tmp_path / "file1.txt").write_text("a")
    (tmp_path / "file2.txt").write_text("b")

    mock_console_print = mocker.patch("bmv.cli.console.print")

    # 构造命名冲突场景（尝试把两个不同文件都重命名为同一个文件名）
    runner.invoke(app, [
        "replace",
        "-p", str(tmp_path),
        "-f", r"file\d",
        "-r", "file_same",
        "--regex"
    ])

    # 查找被打印的 Panel 对象
    printed_panels = [
        call.args[0] for call in mock_console_print.call_args_list 
        if call.args and isinstance(call.args[0], Panel)
    ]

    assert len(printed_panels) >= 1
    panel: Panel = printed_panels[0]

    # 校验面板标题与样式
    assert "Conflict" in str(panel.title) or "冲突" in str(panel.title) or "Error" in str(panel.title)
    assert panel.style == "red" or panel.border_style == "red"


# --- 3. 验证进度条 (Rich Progress) 推进逻辑 ---

def test_progress_bar_execution(tmp_path: Path, mocker: MockerFixture):
    """验证批量重命名执行过程中，Rich Progress 进度条是否被正确创建并按批次推进 (advance)"""
    # 创建 3 个待重命名文件
    for i in range(3):
        (tmp_path / f"test_{i}.txt").write_text("content")

    # Mock Progress 类的 advance 方法
    mock_advance = mocker.patch("rich.progress.Progress.advance")

    result = runner.invoke(app, [
        "replace",
        "-p", str(tmp_path),
        "-f", "test_",
        "-r", "demo_"
    ])

    assert result.exit_code == 0
    # 验证 advance 方法被调用的次数等于重命名的文件数 (3次)
    assert mock_advance.call_count == 3


# --- 4. 验证富文本颜色标记 (Rich Style Text) 打印参数 ---

def test_success_summary_styled_output(tmp_path: Path, mocker: MockerFixture):
    """验证成功完成后 Console.print 是否传入了指定的 rich style 参数（如 green 样式）"""
    (tmp_path / "data.csv").write_text("1,2,3")

    mock_console_print = mocker.patch("bmv.cli.console.print")

    result = runner.invoke(app, [
        "format",
        "-p", str(tmp_path),
        "-st", "kebab"
    ])

    assert result.exit_code == 0

    # 检查是否有使用 [green] 格式控制符或 style="bold green" 的调用
    has_green_styled_call = any(
        "green" in str(call) or "bold" in str(call)
        for call in mock_console_print.call_args_list
    )
    assert has_green_styled_call