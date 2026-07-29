import glob
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


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    pattern: Annotated[
        str | None,
        typer.Argument(help="目标文件匹配模式 (支持 Glob 通配符，如 './videos/*.mp4')", show_default=False),
    ] = None,
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

    # 2. 通过 Glob 规则筛选文件
    matched_paths = [Path(p) for p in glob.glob(pattern, recursive=True) if Path(p).is_file()]
    if not matched_paths:
        console.print(f"[yellow]未找到匹配模式 '[bold]{pattern}[/bold]' 的文件。[/yellow]")
        return

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
        table.add_row(str(action.original_path), action.target_path.name)

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