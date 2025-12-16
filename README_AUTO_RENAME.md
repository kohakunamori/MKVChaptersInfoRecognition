# MKV章节自动识别与重命名工具

自动识别MKV视频文件中每个章节的音乐，并更新章节名称为歌曲信息。

## ✨ 功能特性

- 🎵 自动提取MKV文件的章节信息
- 🔍 使用音频指纹技术识别每个章节的歌曲
- 📝 自动更新章节名称为"歌名 - 歌手"格式
- 💾 支持备份原始章节信息
- 🌐 基于网易云音乐API，识别率高
- ⚙️ 灵活的采样时间配置

## 📋 依赖要求

### 系统工具
- **FFmpeg**: 音频提取（需要在PATH中或指定路径）
- **MKVToolNix**: 章节提取和更新（mkvextract, mkvpropedit）
- **Node.js**: 运行JavaScript音频指纹模块

### Python包
```bash
pip install pythonmonkey pyncm
```

## 🚀 快速开始

### 基本用法

```bash
# 处理MKV文件，自动识别并更新章节
python auto_rename_mkv_chapters.py video.mkv
```

### 高级用法

```bash
# 输出到新文件
python auto_rename_mkv_chapters.py video.mkv -o output.mkv

# 调整采样起始时间（从章节开始10秒后采样）
python auto_rename_mkv_chapters.py video.mkv --offset 10

# 不备份原始章节
python auto_rename_mkv_chapters.py video.mkv --no-backup

# 指定FFmpeg路径（Windows示例）
python auto_rename_mkv_chapters.py video.mkv --ffmpeg "C:/ffmpeg/bin/ffmpeg.exe"

# 指定MKVToolNix路径
python auto_rename_mkv_chapters.py video.mkv --mkvextract "C:/Program Files/MKVToolNix/mkvextract.exe" --mkvpropedit "C:/Program Files/MKVToolNix/mkvpropedit.exe"
```

## 📖 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `mkv_file` | MKV视频文件路径（必需） | - |
| `-o, --output` | 输出文件路径 | 覆盖原文件 |
| `--offset` | 从章节开始后多少秒开始采样 | 5.0 |
| `--no-backup` | 不备份原始章节信息 | False |
| `--ffmpeg` | FFmpeg可执行文件路径 | ffmpeg |
| `--mkvextract` | mkvextract可执行文件路径 | mkvextract |
| `--mkvpropedit` | mkvpropedit可执行文件路径 | mkvpropedit |

## 🔧 工作流程

1. **提取章节** - 从MKV文件中读取现有章节信息
2. **备份数据** - 保存原始章节到 `.chapters.backup.json`
3. **音频采样** - 从每个章节的指定位置提取3秒音频
4. **生成指纹** - 将音频转换为唯一的指纹特征
5. **在线识别** - 通过网易云音乐API匹配歌曲
6. **更新章节** - 将识别结果写入MKV文件

## 📊 章节命名格式

识别成功后，章节名称格式：

```
歌名 - 歌手1, 歌手2
```

如果歌曲有中文译名：

```
歌名（中文译名）- 歌手1, 歌手2
```

### 示例

原始章节：
```
Chapter 01
Chapter 02
Chapter 03
```

处理后：
```
めにしゅき♡ラッシュっしゅ！（超级喜欢♡全力冲击）- 篠原侑, 宮下早紀, 佳原萌枝
きゅんきゅん★デイズ - スペシャルウィーク (CV. 和氣あず未)
Make debut! - スペシャルウィーク (CV. 和氣あず未)
```

## ⚙️ 配置说明

### 采样时间偏移（--offset）

- **用途**: 避开章节开始的静音或前奏部分
- **推荐值**: 
  - 纯音乐：3-5秒
  - 有对白：5-10秒
  - 长前奏：10-15秒

### 音频参数

脚本使用以下固定参数提取音频：
- 采样率：8000 Hz
- 时长：3 秒
- 声道：单声道
- 格式：PCM F32LE

这些参数针对音频指纹识别优化，无需修改。

## 🛠️ 故障排除

### 问题1: 找不到FFmpeg

**错误信息**: `ffmpeg: command not found` 或类似错误

**解决方案**:
```bash
# 方法1: 添加FFmpeg到系统PATH
# 方法2: 使用--ffmpeg参数指定完整路径
python auto_rename_mkv_chapters.py video.mkv --ffmpeg "/path/to/ffmpeg"
```

### 问题2: 找不到MKVToolNix

**错误信息**: `mkvextract: command not found`

**解决方案**:
```bash
# Windows示例
python auto_rename_mkv_chapters.py video.mkv ^
  --mkvextract "C:/Program Files/MKVToolNix/mkvextract.exe" ^
  --mkvpropedit "C:/Program Files/MKVToolNix/mkvpropedit.exe"
```

### 问题3: 无法识别歌曲

**可能原因**:
1. 章节音频质量差（噪音过多）
2. 采样位置不合适（在静音或过渡段）
3. 歌曲不在网易云音乐数据库中

**解决方案**:
1. 调整 `--offset` 参数，尝试不同的采样位置
2. 手动检查章节对应的音频内容
3. 使用其他识别服务或手动命名

### 问题4: pythonmonkey错误

**错误信息**: `ImportError: No module named 'pythonmonkey'`

**解决方案**:
```bash
pip install pythonmonkey
```

如果安装失败，可能需要安装构建工具：
- **Windows**: 安装 Visual Studio Build Tools
- **Linux**: `sudo apt-get install build-essential`
- **macOS**: `xcode-select --install`

## 📂 文件结构

```
AutoClipByMusicRcongniton-ForMKV/
├── auto_rename_mkv_chapters.py      # 主程序
├── ncm-afp/
│   ├── afp.py                        # 音频指纹识别
│   └── docs/
│       └── afp.js                    # JavaScript指纹生成模块
└── README_AUTO_RENAME.md             # 说明文档
```

## 🔒 备份文件

脚本会自动创建备份文件：

- **文件名**: `原文件名.chapters.backup.json`
- **位置**: 与MKV文件同目录
- **内容**: 原始章节的完整信息（JSON格式）

如需恢复原始章节：
```bash
# 可以手动编辑JSON文件，然后使用mkvpropedit恢复
# 或重新运行脚本前删除.mkv文件，使用备份文件
```

## 🎯 使用场景

1. **音乐合集视频** - 自动识别并标注每首歌曲
2. **演唱会录像** - 标记每首歌的名称和艺术家
3. **MV合集** - 快速整理大量MV的章节信息
4. **游戏OST** - 为游戏音乐视频添加详细章节
5. **自动化工作流** - 批量处理大量视频文件

## 💡 高级技巧

### 批量处理多个文件

创建批处理脚本（Windows PowerShell）：

```powershell
# batch_process.ps1
Get-ChildItem -Filter "*.mkv" | ForEach-Object {
    Write-Host "Processing: $($_.Name)"
    python auto_rename_mkv_chapters.py $_.FullName --offset 8
}
```

Linux/macOS (Bash)：

```bash
#!/bin/bash
for file in *.mkv; do
    echo "Processing: $file"
    python3 auto_rename_mkv_chapters.py "$file" --offset 8
done
```

### 自定义章节格式

修改 `_format_chapter_title` 方法以自定义输出格式：

```python
def _format_chapter_title(self, song_info: Dict) -> str:
    # 仅歌名
    return song_info['name']
    
    # 歌名 + 专辑
    return f"{song_info['name']} [{song_info['album']}]"
    
    # 完整信息
    return f"{song_info['name']} - {song_info['artists']} ({song_info['album']})"
```

## 📝 许可证

本工具基于开源项目开发，仅供学习和个人使用。请遵守相关API的使用条款。

## 🙏 致谢

- [pythonmonkey](https://github.com/Distributive-Network/PythonMonkey) - Python与JavaScript互操作
- [pyncm](https://github.com/mos9527/pyncm) - 网易云音乐API
- [MKVToolNix](https://mkvtoolnix.download/) - MKV文件处理工具
- [FFmpeg](https://ffmpeg.org/) - 多媒体处理框架

## 📮 反馈

如有问题或建议，欢迎提出Issue或Pull Request。
