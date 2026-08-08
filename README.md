# BMV (Batch Move / Rename)

**BMV** 是一款高效、安全、基于 Rich 终端可视化的批量文件重命名与标准化整理工具。

BMV 提供了 **字符串/正则替换**、**连结风格转换**、**行业规范预设** 以及 **随机混淆/哈希重命名** 等核心功能，结合对比表格、冲突警告面板与实时进度条，让批量文件整理变得直观、精准且安全。

---

## ✨ 特性亮点

* 🔤 **字符串与正则表达式替换**：支持快速子串替换或基于正则表达式的复杂匹配替换。
* 🏢 **行业规范预设 & 连结风格转换**：
  * 支持 `kebab-case`、`snake_case`、`camelCase`、`PascalCase` 常见连结风格转换。
  * 内置媒体影音 (`media`)、工程建设 (`eng`)、财务行政 (`fin`)、学术论文 (`academic`) 行业标准化命名模板。
* 🎲 **随机混淆与安全重命名**：支持 `uuid`、文件内容 `hash` (MD5) 及 `short` 随机字符混淆，满足隐私保护与唯一性需求。
* 👀 **安全预览与交互确认**：提供 `--dry-run` 预览模式与 `-y / --confirm` 交互确认，防止误操作。
* 🎨 **Rich 终端可视化**：包含 Rich 交互表格、高亮命名冲突警告面板（Panel）及批量处理进度条（Progress）。

---

## 📦 安装指南

### 前置要求
* **Python**: 3.12 或更高版本

---

### 方法一：使用 pipx 安装（推荐 🌟）

```bash
# 从本地源码安装
git clone https://github.com/feelingvi/bmv.git
cd bmv
pipx install .
```

### 方法二：使用标准 pip 安装

```bash
git clone https://github.com/feelingvi/bmv.git
cd bmv

# 以可编辑模式安装（开发者推荐）
pip install -e .
```

安装完成后，在终端中输入 `bmv --help` 验证是否成功。

---

## 🚀 快速上手与使用示例

### 1. 🔤 字符串与正则表达式替换 (`bmv replace`)

#### 示例 1.1：普通文本替换（仅预览）
将 `./downloads` 目录下所有文件中的 `[BD]` 替换为空格，不实际修改磁盘：
```bash
bmv replace -p ./downloads -f "[BD]" -r " " --dry-run
```

#### 示例 1.2：正则表达式匹配替换
将 `./photos` 目录下的 `img_001.jpg` 格式通过正则重命名为 `pic_001.jpg`：
```bash
bmv replace -p ./photos -e jpg -f r"img_(\d+)" -r r"pic_\1" --regex
```

---

### 2. 🏢 风格转换与行业规范预设 (`bmv format`)

#### 示例 2.1：连结风格转换 (Casing Style)
将 `./docs` 目录下的文件名转换为 `kebab-case`（如 `My Draft File.txt` 转换为 `my-draft-file.txt`）：
```bash
bmv format -p ./docs -st kebab
```

#### 示例 2.2：媒体行业规范预设 (Media Preset)
将 `./video` 目录下的视频文件按“项目_场景_日期_序号”格式自动编号重命名：
```bash
bmv format -p ./video -e mp4 -pr media --project "MV" --scene "SC02"
# 生成文件名示例: MV_SC02_20260808_001.mp4
```

#### 示例 2.3：工程建设行业预设 (Engineering Preset)
```bash
bmv format -p ./drawings -pr eng --project "PROJ" --zone "Z01" --disc "ARC" --type "DWG"
# 生成文件名示例: PROJ-Z01-ARC-DWG-001.dwg
```

---

### 3. 🎲 随机/哈希安全重命名 (`bmv random`)

#### 示例 3.1：短随机字符混淆（8位）
```bash
bmv random -p ./temp_files
```

#### 示例 3.2：基于文件内容生成 MD5 Hash 前 10 位重命名
```bash
bmv random -p ./images -e png -m hash -l 10
```

#### 示例 3.3：使用 UUID 重命名
```bash
bmv random -p ./data -m uuid
```

---

## 📖 命令行手册

```text
用法: bmv [COMMAND] [OPTIONS]

命令列表:
  replace   🔤 字符串/正则表达式 批量替换模式
  format    🏢 行业规范化预设 / 连结风格转换 (按 时间>大小 排序递增编号)
  random    🎲 文件名混淆/安全随机重命名

通用选项 (支持所有子命令):
  -p, --path PATH             目标目录路径 (默认: ./)
  -e, --ext TEXT              扩展名过滤 (例如: txt, mp4)
  --reverse                   倒序排列 (默认按 时间>大小 正序)
  -y, --confirm               开启交互式确认提示
  -d, --dry-run               仅预览变更结果，不真正修改文件

replace 命令选项:
  -f, --find TEXT             待查找/替换的字符串或正则表达式
  -r, --replace TEXT          替换后的字符串
  --regex                     开启正则表达式匹配模式

format 命令选项:
  -pr, --preset [media|eng|fin|academic]
                              行业规范预设模式
  -st, --style [kebab|snake|camel|pascal]
                              连结风格转换模式
  --project / --scene / --dept / --type / --author / --disc / --zone
                              预设自定义字段参数

random 命令选项:
  -m, --mode [short|uuid|hash]
                              随机模式 (默认: short)
  -l, --length INTEGER        随机字符或 Hash 截取长度 (默认: 8)
```

---

## 📄 开源与商业授权协议 (License)

本项目采用 **双重授权模式 (Dual Licensing)**：

1. **开源与非商业使用**：
   本项目开源部分采用 [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE) 开源协议。个人用户、教育机构以及开源项目可以免费使用、学习和修改。

2. **商业授权 (Commercial License)**：
   如果你希望将本项目的代码用于**商业产品、闭源软件、公司内部盈利性业务**，或不希望受 AGPL-3.0 强传染性开源条款限制，请联系作者购买商业授权。

* 📧 商业授权与咨询邮箱：`glifelse@gmail.com`