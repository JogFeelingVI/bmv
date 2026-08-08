<!--
 * @Description: 
 * @Author: feelingvi
 * @mail: glifelse#gmail.com
 * @Date: 2026-08-08 17:55:41
 * @LastEditTime: 2026-08-08 17:58:46
 * @LastEditors: YourName
 * @FilePath: /bmv/example.md
-->
**Analyzing bmv Capabilities**

```bash
ls ~/Downloads/chendu
mmexport1785975928573.jpg  
mmexport1785975950247.jpg  
mmexport1785976000132.jpg  
mmexport1785976098975.jpg  
mmexport1785976117522.jpg
mmexport1785975933353.jpg  
mmexport1785975958829.jpg  
mmexport1785976029103.jpg  
mmexport1785976101707.jpg
mmexport1785975945335.jpg  
mmexport1785975972959.jpg  
mmexport1785976079627.jpg  
mmexport1785976104298.jpg
```

> 💡 **提示**：建议在命令末尾加上 `-d` 或 `--dry-run` 进行**安全预览**，确认对比表格无误后再去掉 `-d` 真正执行修改。

---

### 方案一：将微信导出的前缀 `mmexport` 替换为有意义的名称（推荐 ⭐️）

将 `mmexport17859...jpg` 替换为 `chengdu_17859...jpg`：

```bash
# 1. 先预览（不实际修改磁盘）
bmv replace -p ~/Downloads/chendu -f "mmexport" -r "chengdu_" -d

# 2. 确认无误后，去掉 -d 实际执行重命名
bmv replace -p ~/Downloads/chendu -f "mmexport" -r "chengdu_"
```

如果你想把前面这一串乱码的时间戳整体换掉，只保留关键信息：
```bash
# 正则匹配：将 mmexport + 数字 替换为 chengdu_photo
bmv replace -p ~/Downloads/chendu -e jpg -f r"mmexport\d+" -r "chengdu_photo" --regex -d
```

---

### 方案二：按递增序号重命名（如 `001_mmexport...jpg` 或 `chengdu_001.jpg`）

如果你希望按文件的时间/大小顺序给图片排编号（`001`, `002`, `003`...）：

#### 2.1 自动加上三位递增编号前缀
```bash
bmv format -p ~/Downloads/chendu -e jpg -d
# 结果示例: 001_mmexport1785975928573.jpg
```

#### 2.2 使用媒体标准化模板预设 (Media Preset)
将所有图片格式化为 `成都项目_照片场景_当天日期_序号.jpg`：
```bash
bmv format -p ~/Downloads/chendu -e jpg -pr media --project "Chengdu" --scene "Photo" -d
# 结果示例: Chengdu_Photo_20260808_001.jpg, Chengdu_Photo_20260808_002.jpg ...
```

---

### 方案三：根据图片文件内容计算 Hash 重命名（防止重复）

基于文件内容生成 MD5 Hash 值前 8 位重命名（适合去重和存档）：

```bash
bmv random -p ~/Downloads/chendu -e jpg -m hash -l 8 -d
# 结果示例: a1b2c3d4.jpg, e5f6g7h8.jpg ...
```

---

### 💡 常用参数说明

* `-p ~/Downloads/chendu`：指定目标文件夹目录
* `-e jpg`：仅筛选扩展名为 `.jpg` 的文件
* `-d` / `--dry-run`：**仅预览修改**，不影响真实磁盘文件
* `-y` / `--confirm`：执行前开启交互提示框再次确认