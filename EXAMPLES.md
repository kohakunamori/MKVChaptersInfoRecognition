# 使用示例

本文档展示了如何使用MKV章节自动识别工具的各种使用场景。

## 📋 前置准备

### 1. 安装依赖

```bash
# 安装Python包
pip install pythonmonkey pyncm

# 确保已安装以下系统工具:
# - FFmpeg
# - MKVToolNix (mkvextract, mkvpropedit)
# - Node.js
```

### 2. 验证工具可用

```bash
# 测试FFmpeg
ffmpeg -version

# 测试MKVToolNix
mkvextract --version
mkvpropedit --version

# 测试Node.js
node --version
```

## 🎯 使用场景

### 场景1: 处理单个MKV文件

最简单的用法，处理一个MKV文件：

```bash
python auto_rename_mkv_chapters.py "video.mkv"
```

处理后：
- ✅ 章节名称已更新
- 💾 原始章节备份到 `video.chapters.backup.json`
- 📝 原文件被直接修改

---

### 场景2: 输出到新文件（保留原文件）

如果你想保留原始文件：

```bash
python auto_rename_mkv_chapters.py "video.mkv" -o "video_renamed.mkv"
```

结果：
- 原文件：`video.mkv` (未修改)
- 新文件：`video_renamed.mkv` (已更新章节)

---

### 场景3: 调整采样位置

有些章节开始有长时间的静音或对白，需要延后采样：

```bash
# 从章节开始10秒后采样
python auto_rename_mkv_chapters.py "video.mkv" --offset 10

# 从章节开始3秒后采样（对于纯音乐视频）
python auto_rename_mkv_chapters.py "video.mkv" --offset 3
```

**推荐值：**
- 纯音乐MV合集：3-5秒
- 有主持人介绍的演唱会：8-15秒
- 游戏配乐视频：5-8秒

---

### 场景4: Windows下指定工具路径

Windows系统通常需要指定完整路径：

```powershell
python auto_rename_mkv_chapters.py "video.mkv" `
  --ffmpeg "C:/ffmpeg/bin/ffmpeg.exe" `
  --mkvextract "C:/Program Files/MKVToolNix/mkvextract.exe" `
  --mkvpropedit "C:/Program Files/MKVToolNix/mkvpropedit.exe"
```

---

### 场景5: 批量处理目录

处理一个目录下的所有MKV文件：

```bash
# 处理当前目录
python batch_process.py .

# 处理指定目录
python batch_process.py "/path/to/videos"

# 递归处理所有子目录
python batch_process.py "/path/to/videos" -r
```

---

### 场景6: 重新处理已处理过的文件

默认情况下，脚本会跳过已有备份文件的视频。如需重新处理：

```bash
# 单文件模式：删除备份文件后重新运行
rm video.chapters.backup.json
python auto_rename_mkv_chapters.py "video.mkv"

# 批量模式：使用--no-skip参数
python batch_process.py "/path/to/videos" --no-skip
```

---

## 🔧 实际案例

### 案例1: 演唱会视频

文件：`concert_2024.mkv`

现状：
```
Chapter 01: 开场
Chapter 02: Track 02
Chapter 03: Track 03
...
```

命令：
```bash
# 演唱会通常有主持人介绍，延后10秒采样
python auto_rename_mkv_chapters.py "concert_2024.mkv" --offset 10
```

结果：
```
Chapter 01: 开场
Chapter 02: Rising Sun - EXILE
Chapter 03: Lovers Again - EXILE
...
```

---

### 案例2: 游戏OST合集

文件：`game_ost_collection.mkv`

现状：
```
Chapter 1
Chapter 2
Chapter 3
```

命令：
```bash
# 游戏OST通常是纯音乐，5秒采样即可
python auto_rename_mkv_chapters.py "game_ost_collection.mkv" --offset 5
```

结果：
```
めにしゅき♡ラッシュっしゅ！（超级喜欢♡全力冲击）- 篠原侑, 宮下早紀, 佳原萌枝
NEXT FRONTIER - スペシャルウィーク (CV. 和氣あず未)
Make debut! - スペシャルウィーク (CV. 和氣あず未)
```

---

### 案例3: 批量处理整个音乐视频库

目录结构：
```
Music_Videos/
├── Artist_A/
│   ├── concert1.mkv
│   └── concert2.mkv
├── Artist_B/
│   └── live_show.mkv
└── Compilations/
    ├── top100_2023.mkv
    └── top100_2024.mkv
```

命令：
```bash
# 递归处理所有子目录
python batch_process.py "Music_Videos" -r --offset 8
```

输出：
```
找到 5 个MKV文件
需要处理: 5 个文件

[1/5] 开始处理: concert1.mkv
✅ 完成: concert1.mkv

[2/5] 开始处理: concert2.mkv
✅ 完成: concert2.mkv

...

📊 处理完成
总文件数: 5
成功: 5
失败: 0
跳过: 0
```

---

## 📝 PowerShell脚本示例

### 批量处理脚本（Windows）

创建 `batch_rename.ps1`:

```powershell
# 配置
$VideoDir = "C:\Users\YourName\Videos\Music"
$FFmpegPath = "C:\ffmpeg\bin\ffmpeg.exe"
$MKVExtract = "C:\Program Files\MKVToolNix\mkvextract.exe"
$MKVPropEdit = "C:\Program Files\MKVToolNix\mkvpropedit.exe"
$Offset = 8

# 查找所有MKV文件
$MkvFiles = Get-ChildItem -Path $VideoDir -Filter "*.mkv" -Recurse

Write-Host "找到 $($MkvFiles.Count) 个MKV文件" -ForegroundColor Green

$Count = 0
foreach ($File in $MkvFiles) {
    $Count++
    Write-Host "`n[$Count/$($MkvFiles.Count)] 处理: $($File.Name)" -ForegroundColor Cyan
    
    python auto_rename_mkv_chapters.py `
        $File.FullName `
        --offset $Offset `
        --ffmpeg $FFmpegPath `
        --mkvextract $MKVExtract `
        --mkvpropedit $MKVPropEdit
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 失败" -ForegroundColor Red
    }
}

Write-Host "`n全部完成！" -ForegroundColor Green
```

运行：
```powershell
powershell -ExecutionPolicy Bypass -File batch_rename.ps1
```

---

### Bash脚本示例（Linux/macOS）

创建 `batch_rename.sh`:

```bash
#!/bin/bash

# 配置
VIDEO_DIR="/home/user/Videos/Music"
OFFSET=8

# 查找所有MKV文件
find "$VIDEO_DIR" -name "*.mkv" | while read -r file; do
    echo ""
    echo "处理: $(basename "$file")"
    
    python3 auto_rename_mkv_chapters.py \
        "$file" \
        --offset "$OFFSET"
    
    if [ $? -eq 0 ]; then
        echo "✅ 成功"
    else
        echo "❌ 失败"
    fi
done

echo ""
echo "全部完成！"
```

运行：
```bash
chmod +x batch_rename.sh
./batch_rename.sh
```

---

## 🎨 自定义章节格式

如果你想自定义章节名称格式，可以修改 `auto_rename_mkv_chapters.py` 中的 `_format_chapter_title` 方法：

### 格式1: 仅歌名

```python
def _format_chapter_title(self, song_info: Dict) -> str:
    return song_info['name']
```

结果：
```
めにしゅき♡ラッシュっしゅ！
きゅんきゅん★デイズ
Make debut!
```

---

### 格式2: 歌名 + 专辑

```python
def _format_chapter_title(self, song_info: Dict) -> str:
    return f"{song_info['name']} [{song_info['album']}]"
```

结果：
```
めにしゅき♡ラッシュっしゅ！ [めにしゅき♡ラッシュっしゅ！]
きゅんきゅん★デイズ [WINNING LIVE 01]
```

---

### 格式3: 完整信息

```python
def _format_chapter_title(self, song_info: Dict) -> str:
    artists = song_info['artists']
    album = song_info['album']
    name = song_info['name']
    
    return f"{name} - {artists} ({album})"
```

结果：
```
めにしゅき♡ラッシュっしゅ！ - 篠原侑, 宮下早紀 (めにしゅき♡ラッシュっしゅ！)
```

---

## 🔍 调试技巧

### 查看详细错误信息

如果识别失败，查看 `batch_process.log` 文件：

```bash
# 实时查看日志
tail -f batch_process.log

# 搜索错误
grep "ERROR" batch_process.log
grep "失败" batch_process.log
```

---

### 手动测试音频提取

验证FFmpeg是否正常工作：

```bash
# 提取3秒音频样本到文件
ffmpeg -ss 5 -i "video.mkv" -t 3 \
  -acodec pcm_f32le -f f32le -ar 8000 -ac 1 \
  test_sample.raw

# 检查文件大小（应该是96000字节）
ls -lh test_sample.raw
```

---

### 手动测试章节提取

验证MKVToolNix是否正常：

```bash
# 提取章节到XML
mkvextract "video.mkv" chapters chapters.xml

# 查看章节内容
cat chapters.xml
```

---

## 💡 优化建议

### 1. 提高识别准确率

- 选择歌曲高潮部分采样（通常在开始后30-60秒）
- 避开对白、静音、过渡音效
- 确保音频质量良好（无噪音）

### 2. 加快处理速度

- 批量处理时使用单线程（避免API限流）
- 跳过已处理的文件（使用备份文件判断）
- 使用SSD存储临时文件

### 3. 节省存储空间

- 直接修改原文件（不使用-o参数）
- 处理完成后删除备份文件（如不需要）
- 压缩日志文件

---

## 🆘 常见问题

**Q: 为什么有些章节无法识别？**

A: 可能原因：
1. 采样位置不合适（试试调整--offset）
2. 歌曲不在网易云数据库
3. 音频质量差或有噪音
4. 网络问题导致API请求失败

**Q: 可以同时处理多个文件吗？**

A: 可以，但不建议。网易云API有频率限制，并发请求可能导致封禁。建议使用单线程批量处理。

**Q: 如何恢复原始章节？**

A: 方法1：使用备份文件 `.chapters.backup.json` 手动恢复
   方法2：重新从原始视频源提取章节

**Q: 支持其他音乐识别服务吗？**

A: 目前仅支持网易云音乐。如需其他服务，需要修改 `AudioRecognizer` 类的 `recognize_song` 方法。

---

## 📚 更多资源

- [FFmpeg官方文档](https://ffmpeg.org/documentation.html)
- [MKVToolNix用户手册](https://mkvtoolnix.download/doc/mkvtoolnix.html)
- [pyncm项目地址](https://github.com/mos9527/pyncm)
- [pythonmonkey文档](https://github.com/Distributive-Network/PythonMonkey)
