"""
Description:
Author: feelingvi
mail: glifelse#gmail.com
Date: 2026-07-29 16:27:28
LastEditTime: 2026-08-08 11:01:58
LastEditors: YourName
FilePath: /bmv/src/bmv/cli.py
"""

import re
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from bmv.engine import BMVEngine, CaseStyle, IndustryPreset, RandomMode

app = typer.Typer(
    name="bmv",
    help="🚀 高效、安全的批量文件重命名与标准化整理工具",
    add_completion=False,
)
console = Console()


def run_rename_pipeline(
    engine: BMVEngine,
    rename_plan: list[tuple[Path, Path]],
    dry_run: bool,
    confirm: bool = False,
):
    if not rename_plan:
        console.print("[yellow]💡 没有发现需要修改的文件。[/yellow]")
        return

    targets = [dst for _, dst in rename_plan]
    if len(targets) != len(set(targets)):
        console.print(
            Panel(
                "生成的目标文件名存在重复！请调整参数。",
                title="[bold red]命名冲突[/bold red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    table = Table(
        title="[Dry-Run 模拟结果]" if dry_run else "[执行结果]", show_lines=True
    )
    table.add_column("原文件名", style="cyan")
    table.add_column("重命名后", style="green")

    for src, dst in rename_plan:
        table.add_row(src.name, dst.name)

    console.print(table)

    if dry_run:
        console.print(
            f"\n[bold yellow]👀 Dry-Run 模式:[/bold yellow] 预览了 {len(rename_plan)} 个文件，未修改实际磁盘文件。"
        )
        return

    # 若指定了 --confirm 标志，在此触发交互式询问
    if confirm and not typer.confirm("确认要执行重命名操作吗？"):
        console.print("[yellow]已取消操作。[/yellow]")
        raise typer.Exit(code=1)

    success_count = 0
    try:
        with Progress() as progress:
            task = progress.add_task("[green]重命名中...", total=len(rename_plan))
            for src, dst in rename_plan:
                if src != dst:
                    src.rename(dst)
                    success_count += 1
                progress.advance(task)
    except OSError as e:
        console.print(f"[red]❌ 失败 {src.name}: {e}[/red]")

    console.print(
        f"\n[bold green]✅ 成功完成![/bold green] 已将 {success_count} 个文件重命名。"
    )


@app.command("replace")
def replace_cmd(
    path: Annotated[Path, typer.Option("-p", "--path", help="目标目录")] = Path("./"),
    ext: Annotated[str, typer.Option("-e", "--ext", help="扩展名过滤")] = "",
    find: Annotated[str, typer.Option("-f", "--find", help="待替换的字符")] = "",
    replace: Annotated[str, typer.Option("-r", "--replace", help="替换后的字符")] = "",
    regex: Annotated[bool, typer.Option("--regex", help="是否开启正则表达式")] = False,
    reverse: Annotated[
        bool, typer.Option("--reverse", help="倒序排列（默认按时间>大小正序）")
    ] = False,
    confirm: Annotated[
        bool, typer.Option("-y", "--confirm", help="开启交互式确认提示")
    ] = False,
    dry_run: Annotated[bool, typer.Option("-d", "--dry-run", help="仅预览结果")] = False,
):
    """🔤 字符串/正则表达式 批量替换模式"""
    try:
        engine = BMVEngine(path, ext, reverse)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    files = engine.collect_and_sort_files()

    plan = [
        (
            f,
            f.parent
            / f"{(re.sub(find, replace, f.stem) if regex else f.stem.replace(find, replace))}{f.suffix}",
        )
        for f in files
    ]
    run_rename_pipeline(engine, plan, dry_run, confirm)


@app.command("format")
def format_cmd(
    path: Annotated[Path, typer.Option("-p", "--path", help="目标目录")] = Path("./"),
    ext: Annotated[str, typer.Option("-e", "--ext", help="扩展名过滤")] = "",
    preset: Annotated[
        IndustryPreset | None,
        typer.Option("-pr", "--preset", help="行业规范化预设模式"),
    ] = None,
    style: Annotated[
        CaseStyle | None,
        typer.Option("-st", "--style", help="连结风格转换模式"),
    ] = None,
    project: Annotated[
        str | None, typer.Option("--project", help="[预设参数] 项目代号")
    ] = None,
    scene: Annotated[
        str | None, typer.Option("--scene", help="[预设参数] 场景代号")
    ] = None,
    dept: Annotated[
        str | None, typer.Option("--dept", help="[预设参数] 部门名称")
    ] = None,
    doc_type: Annotated[
        str | None, typer.Option("--type", help="[预设参数] 文档类型")
    ] = None,
    author: Annotated[
        str | None, typer.Option("--author", help="[预设参数] 作者/责任人")
    ] = None,
    disc: Annotated[
        str | None, typer.Option("--disc", help="[预设参数] 专业代码")
    ] = None,
    zone: Annotated[
        str | None, typer.Option("--zone", help="[预设参数] 分区代码")
    ] = None,
    reverse: Annotated[bool, typer.Option("--reverse", help="倒序排列")] = False,
    confirm: Annotated[
        bool, typer.Option("-y", "--confirm", help="开启交互式确认提示")
    ] = False,
    dry_run: Annotated[bool, typer.Option("-d", "--dry-run", help="仅预览修改")] = False,
):
    """🏢 行业规范化预设 / 连结风格转换 (按 时间>大小 排序递增编号)"""
    try:
        engine = BMVEngine(path, ext, reverse)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    files = engine.collect_and_sort_files()
    extra_args = {
        "project": project,
        "scene": scene,
        "dept": dept,
        "doc_type": doc_type,
        "author": author,
        "disc": disc,
        "zone": zone,
    }

    plan = []
    for idx, f in enumerate(files, start=1):
        if preset:
            new_stem = engine.format_industry_name(preset, idx, extra_args)
        elif style:
            new_stem = engine.to_casing(f.stem, style)
        else:
            new_stem = f"{idx:03d}_{f.stem}"
        plan.append((f, f.parent / f"{new_stem}{f.suffix}"))

    run_rename_pipeline(engine, plan, dry_run, confirm)


@app.command("random")
def random_cmd(
    path: Annotated[Path, typer.Option("-p", "--path", help="目标目录")] = Path("./"),
    ext: Annotated[str | None, typer.Option("-e", "--ext", help="扩展名过滤")] = None,
    mode: Annotated[
        RandomMode, typer.Option("-m", "--mode", help="随机模式: uuid/hash/short")
    ] = RandomMode.short,
    length: Annotated[int, typer.Option("-l", "--length", help="随机字符/Hash长度")] = 8,
    reverse: Annotated[bool, typer.Option("--reverse", help="倒序排列")] = False,
    confirm: Annotated[
        bool, typer.Option("-y", "--confirm", help="开启交互式确认提示")
    ] = False,
    dry_run: Annotated[bool, typer.Option("-d", "--dry-run", help="仅预览修改")] = False,
):
    """🎲 文件名混淆/安全随机重命名"""
    try:
        engine = BMVEngine(path, ext, reverse)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    files = engine.collect_and_sort_files()
    plan = [
        (f, f.parent / f"{engine.generate_random_name(f, mode, length)}{f.suffix}")
        for f in files
    ]
    run_rename_pipeline(engine, plan, dry_run, confirm)


if __name__ == "__main__":
    app()