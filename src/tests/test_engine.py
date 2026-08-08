import os
import time
from pathlib import Path

import pytest

from bmv.engine import BMVEngine, CaseStyle, IndustryPreset, RandomMode

# --- 1. 测试 双重排序 (时间 > 大小) ---

def test_sort_files_by_time_and_size(tmp_path: Path):
    """验证文件是否严格按照 修改时间(mtime) > 文件大小(size) 排序"""
    # 1. 创建 3 个临时文件
    file_old = tmp_path / "old.txt"
    file_new_small = tmp_path / "new_small.txt"
    file_new_large = tmp_path / "new_large.txt"

    file_old.write_text("old content")
    time.sleep(0.05)  # 确保 mtime 有微小时间差

    # 写入不同大小的内容
    file_new_small.write_text("A")  # 1 byte
    file_new_large.write_text("AAAAA")  # 5 bytes

    # 强制修改 mtime，使 new_small 和 new_large 的时间完全一致
    now = time.time()
    os.utime(file_old, (now - 100, now - 100))
    os.utime(file_new_small, (now, now))
    os.utime(file_new_large, (now, now))

    # 执行引擎排序
    engine = BMVEngine(target_dir=tmp_path, ext=".txt")
    sorted_files = engine.collect_and_sort_files()

    # 预期顺序: old.txt -> new_small.txt (时间相同大小小) -> new_large.txt (时间相同大小大)
    expected_order = [file_old, file_new_small, file_new_large]
    assert sorted_files == expected_order

    # 测试倒序
    engine_reverse = BMVEngine(target_dir=tmp_path, ext=".txt", reverse=True)
    assert engine_reverse.collect_and_sort_files() == list(reversed(expected_order))


# --- 2. 测试 连结风格转换 (Casing) ---

@pytest.mark.parametrize("input_text, style, expected", [
    ("hello world", CaseStyle.kebab, "hello-world"),
    ("hello_world_test", CaseStyle.kebab, "hello-world-test"),
    ("MyProjectFile", CaseStyle.snake, "my_project_file"),
    ("user-profile-photo", CaseStyle.camel, "userProfilePhoto"),
    ("convert_this_string", CaseStyle.pascal, "ConvertThisString"),
])
def test_to_casing(input_text, style, expected):
    result = BMVEngine.to_casing(input_text, style)
    assert result == expected


# --- 3. 测试 行业标准化预设模板 ---

def test_format_industry_name_media(tmp_path: Path):
    extra = {"project": "MV", "scene": "SC02"}
    res = BMVEngine.format_industry_name(IndustryPreset.media, index=1, extra=extra)
    # 期望格式: MV_SC02_YYYYMMDD_001
    assert res.startswith("MV_SC02_")
    assert res.endswith("_001")

def test_format_industry_name_engineering(tmp_path: Path):
    extra = {"project": "PRJ", "zone": "Z01", "disc": "ARC", "doc_type": "DR"}
    res = BMVEngine.format_industry_name(IndustryPreset.eng, index=5, extra=extra)
    assert res == "PRJ-Z01-ARC-DR-005"

def test_format_industry_name_academic(tmp_path: Path):
    extra = {"author": "Zhang", "doc_type": "Paper"}
    res = BMVEngine.format_industry_name(IndustryPreset.academic, index=12, extra=extra)
    # 期望格式: Zhang_2026_Paper_012
    assert "Zhang_" in res
    assert res.endswith("_012")


# --- 4. 测试 随机命名 ---

def test_generate_random_name_short(tmp_path: Path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    name = BMVEngine.generate_random_name(f, mode=RandomMode.short, length=10)
    assert len(name) == 10

def test_generate_random_name_uuid(tmp_path: Path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    name = BMVEngine.generate_random_name(f, mode=RandomMode.uuid, length=8)
    assert len(name) == 36  # 标准 UUID 字符串长度

def test_generate_random_name_hash(tmp_path: Path):
    f = tmp_path / "test.txt"
    f.write_text("content for hash")
    hash_name1 = BMVEngine.generate_random_name(f, mode=RandomMode.hash, length=8)
    assert len(hash_name1) == 8
    
    # 验证相同内容生成的哈希相同（幂等性）
    hash_name2 = BMVEngine.generate_random_name(f, mode=RandomMode.hash, length=8)
    assert hash_name1 == hash_name2


# --- 5. 测试 扩展名过滤 ---

def test_ext_filtering(tmp_path: Path):
    (tmp_path / "a.png").write_text("img")
    (tmp_path / "b.txt").write_text("txt")

    engine = BMVEngine(target_dir=tmp_path, ext="png")
    files = engine.collect_and_sort_files()
    
    assert len(files) == 1
    assert files[0].name == "a.png"