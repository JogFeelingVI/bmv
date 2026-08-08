"""
Description:
Author: feelingvi
mail: glifelse#gmail.com
Date: 2026-07-29 16:27:18
LastEditTime: 2026-08-08 10:33:00
LastEditors: YourName
FilePath: /bmv/src/bmv/engine.py
"""

import hashlib
import re
import secrets
import uuid
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path


class IndustryPreset(str, Enum):
    media = "media"
    eng = "eng"
    fin = "fin"
    academic = "academic"


class CaseStyle(str, Enum):
    kebab = "kebab"
    snake = "snake"
    camel = "camel"
    pascal = "pascal"


class RandomMode(str, Enum):
    short = "short"
    uuid = "uuid"
    hash = "hash"


class BMVEngine:
    def __init__(self, target_dir: Path, ext: str | None = None, reverse: bool = False):
        self.target_dir = target_dir.resolve()
        self.ext = f".{ext.lstrip('.')}".lower() if ext else None
        self.reverse = reverse

        if not self.target_dir.is_dir():
            raise ValueError(f"路径 '{target_dir}' 不是有效目录！")

    def collect_and_sort_files(self) -> list[Path]:
        files = [
            p
            for p in self.target_dir.iterdir()
            if p.is_file() and (not self.ext or p.suffix.lower() == self.ext)
        ]

        def sort_key(p: Path):
            try:
                stat = p.stat()
                return (stat.st_mtime, stat.st_size)
            except OSError:
                return (0, 0)

        return sorted(files, key=sort_key, reverse=self.reverse)

    @staticmethod
    def to_casing(text: str, style: CaseStyle) -> str:
        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|[0-9]+", text)
        if not words:
            words = [text]

        if style == CaseStyle.kebab:
            return "-".join(w.lower() for w in words)
        elif style == CaseStyle.snake:
            return "_".join(w.lower() for w in words)
        elif style == CaseStyle.camel:
            return words[0].lower() + "".join(w.capitalize() for w in words[1:])
        elif style == CaseStyle.pascal:
            return "".join(w.capitalize() for w in words)
        return text

    @staticmethod
    def generate_random_name(file_path: Path, mode: RandomMode, length: int) -> str:
        if mode == RandomMode.uuid:
            return str(uuid.uuid4())
        elif mode == RandomMode.hash:
            hasher = hashlib.md5()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()[:length]
        else:
            return (
                secrets.token_urlsafe(length)[:length]
                .replace("-", "a")
                .replace("_", "b")
            )

    @staticmethod
    def format_industry_name(preset: IndustryPreset, index: int, extra: dict) -> str:
        today = datetime.now(UTC).strftime("%Y%m%d")
        idx_str = f"{index:03d}"

        proj = extra.get("project") or "PROJ"
        scene = extra.get("scene") or "SC01"
        dept = extra.get("dept") or "FIN"
        doc_type = extra.get("doc_type") or "DOC"
        author = extra.get("author") or "Author"
        disc = extra.get("disc") or "ARC"
        zone = extra.get("zone") or "Z01"

        if preset == IndustryPreset.media:
            return f"{proj}_{scene}_{today}_{idx_str}"
        elif preset == IndustryPreset.eng:
            return f"{proj}-{zone}-{disc}-{doc_type}-{idx_str}"
        elif preset == IndustryPreset.fin:
            return f"{today}_{dept}_{doc_type}_{idx_str}"
        elif preset == IndustryPreset.academic:
            year = datetime.now(UTC).year
            return f"{author}_{year}_{doc_type}_{idx_str}"
        return f"FILE_{today}_{idx_str}"
