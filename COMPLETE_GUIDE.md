# 🚀 MKV章节自动识别工具 - 完整功能指南

> 自动识别MKV视频章节中的音乐信息，并重命名为规范的章节标题

---

## 📋 目录

- [快速开始](#快速开始)
- [配置文件方式](#配置文件方式)
- [命令行参数方式](#命令行参数方式)
- [功能详解](#功能详解)
- [完整示例](#完整示例)

---

## ⚡ 快速开始

### 最简单的用法

```bash
# 使用默认设置处理视频
python auto_rename_mkv_chapters.py video.mkv
```

### 查看帮助

```bash
# 查看所有可用参数
python auto_rename_mkv_chapters.py --help

# 查看可用模板
python auto_rename_mkv_chapters.py --list-templates

# 查看模板变量
python auto_rename_mkv_chapters.py --show-variables
```

---

## 📄 配置文件方式

### 优势

✅ **集中管理** - 所有配置在一个文件中  
✅ **可重用** - 批量处理时无需重复输入  
✅ **版本控制** - 配置文件可纳入Git  
✅ **团队协作** - 共享标准化配置  
✅ **易于维护** - 修改配置更方便

### 创建配置文件

```bash
# 创建默认配置文件（包含所有可配置项）
python auto_rename_mkv_chapters.py --create-config my_config.json
```

### 配置文件结构

```json
{
  "mkv_file": "video.mkv",
  "output": null,
  "template": "default",
  "custom_template": null,
  "recognition": {
    "strategy": "start",
    "offset": 5.0,
    "percentage": 0.5,
    "duration": 3
  },
  "tools": {
    "ffmpeg": null,
    "mkvextract": null,
    "mkvpropedit": null
  },
  "options": {
    "no_backup": false,
    "skip_check": false
  }
}
```

### 配置项说明

#### 1. 基本设置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `mkv_file` | string | null | 输入的MKV视频文件路径 |
| `output` | string | null | 输出文件路径（null表示覆盖原文件） |
| `template` | string | "default" | 预设章节模板名称 |
| `custom_template` | string | null | 自定义模板字符串 |

**可用的预设模板**：
- `default` - `{name} - {artists}` - 标准格式
- `simple` - `{name}` - 仅歌名
- `with_trans` - `{name}（{trans_name}）- {artists}` - 带译名
- `full` - `{name} - {artists} [{album}]` - 完整信息
- `artist_first` - `{artists} - {name}` - 歌手优先
- `minimal` - `{name}` - 极简格式
- `with_id` - `{name} - {artists} (ID:{id})` - 含歌曲ID
- `detailed` - `{name}（{trans_name}）- {artists} [{album}] ♡{popularity}` - 详细信息
- `japanese` - `{name} / {artists}` - 日式格式

**模板变量**：
- `{name}` - 歌曲名称
- `{trans_name}` - 中文译名
- `{artists}` - 所有歌手（逗号分隔）
- `{artist_first}` - 第一个歌手
- `{album}` - 专辑名称
- `{id}` - 歌曲ID
- `{popularity}` - 热度值

#### 2.  音乐识别方法 (recognition)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `strategy` | string | "start" | 采样策略 |
| `offset` | number | 5.0 | START策略的延迟秒数 |
| `percentage` | number | 0.5 | CUSTOM策略的位置比例 |
| `duration` | number | 3 | 采样时长（秒） |

**识别策略示例**：

- **start** (从开始)
  ```json
  {
    "strategy": "start",
    "offset": 5.0
  }
  ```
  从章节开始后5秒处采样（跳过前奏）

- **middle** (从中间)
  ```json
  {
    "strategy": "middle"
  }
  ```
  从章节中间位置采样（适合大部分场景）

- **end** (从末尾)
  ```json
  {
    "strategy": "end"
  }
  ```
  从章节末尾采样（适合尾奏特征明显的歌曲）

- **custom** (自定义位置)
  ```json
  {
    "strategy": "custom",
    "percentage": 0.3
  }
  ```
  从章节30%位置采样（0.0-1.0之间）

#### 3. 工具路径 (tools)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `ffmpeg` | string | null | FFmpeg可执行文件路径 |
| `mkvextract` | string | null | mkvextract可执行文件路径 |
| `mkvpropedit` | string | null | mkvpropedit可执行文件路径 |

> 💡 设置为 `null` 时会自动检测系统中的工具路径

手动指定示例：
```json
{
  "tools": {
    "ffmpeg": "C:/Program Files/ffmpeg/bin/ffmpeg.exe",
    "mkvextract": "C:/Program Files/MKVToolNix/mkvextract.exe",
    "mkvpropedit": "C:/Program Files/MKVToolNix/mkvpropedit.exe"
  }
}
```

#### 4. 其他选项 (options)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `no_backup` | boolean | false | 是否禁用自动备份 |
| `skip_check` | boolean | false | 是否跳过工具依赖检查 |

### 使用配置文件

#### 基本用法

```bash
# 完全使用配置文件
python auto_rename_mkv_chapters.py --config my_config.json
```

#### 配置文件 + 命令行覆盖

```bash
# 配置文件中的设置会被命令行参数覆盖
python auto_rename_mkv_chapters.py --config my_config.json video2.mkv --template simple
```

**优先级**: 命令行参数 > 配置文件 > 默认值

### 配置文件示例

#### 示例1: 音乐会视频配置

```json
{
  "template": "full",
  "recognition": {
    "strategy": "middle",
    "duration": 5
  },
  "options": {
    "no_backup": false
  },
  "_comments": {
    "说明": "音乐会视频专用配置",
    "strategy": "从中间采样，避开前奏和尾奏",
    "duration": "5秒采样，提高识别准确度"
  }
}
```

使用：
```bash
python auto_rename_mkv_chapters.py --config concert.json concert_video.mkv
```

#### 示例2: MV合集配置

```json
{
  "template": "simple",
  "recognition": {
    "strategy": "start",
    "offset": 10.0
  },
  "options": {
    "no_backup": false
  },
  "_comments": {
    "说明": "MV合集专用配置",
    "strategy": "跳过10秒前奏，从主歌部分开始识别"
  }
}
```

#### 示例3: 批量处理配置

```json
{
  "template": "with_trans",
  "recognition": {
    "strategy": "middle",
    "duration": 4
  },
  "options": {
    "no_backup": false
  }
}
```

批处理脚本（PowerShell）：
```powershell
Get-ChildItem *.mkv | ForEach-Object {
    python auto_rename_mkv_chapters.py --config batch.json $_.FullName
}
```

#### 示例4: 自定义模板配置

```json
{
  "custom_template": "♪ {name} by {artist_first}",
  "recognition": {
    "strategy": "middle",
    "duration": 3
  }
}
```

---

## 💻 命令行参数方式

### 优势

✅ **快速测试** - 无需创建配置文件  
✅ **灵活调整** - 动态修改参数  
✅ **脚本友好** - 易于脚本化  
✅ **覆盖配置** - 临时覆盖配置文件设置

### 完整参数列表

```bash
python auto_rename_mkv_chapters.py [选项] mkv_file
```

#### 1. 文件参数

```bash
# 基本用法
python auto_rename_mkv_chapters.py video.mkv

# 指定输出文件
python auto_rename_mkv_chapters.py video.mkv -o output.mkv
python auto_rename_mkv_chapters.py video.mkv --output output.mkv
```

| 参数 | 说明 | 示例 |
|------|------|------|
| `mkv_file` | 输入MKV文件（位置参数） | `video.mkv` |
| `-o, --output` | 输出文件路径 | `-o output.mkv` |

#### 2. 识别策略参数

```bash
# 从开始采样（默认，跳过5秒）
python auto_rename_mkv_chapters.py video.mkv --strategy start --offset 10

# 从中间采样
python auto_rename_mkv_chapters.py video.mkv --strategy middle

# 从末尾采样
python auto_rename_mkv_chapters.py video.mkv --strategy end

# 自定义位置采样（30%位置）
python auto_rename_mkv_chapters.py video.mkv --strategy custom --percentage 0.3

# 自定义采样时长
python auto_rename_mkv_chapters.py video.mkv --duration 5
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--strategy` | string | start | 采样策略：start/middle/end/custom |
| `--offset` | float | 5.0 | START策略的延迟秒数 |
| `--percentage` | float | 0.5 | CUSTOM策略的位置比例(0.0-1.0) |
| `--duration` | int | 3 | 采样时长（秒） |

#### 3. 章节模板参数

```bash
# 使用预设模板
python auto_rename_mkv_chapters.py video.mkv --template simple
python auto_rename_mkv_chapters.py video.mkv --template with_trans
python auto_rename_mkv_chapters.py video.mkv --template full

# 使用自定义模板
python auto_rename_mkv_chapters.py video.mkv --template "{name} by {artists}"
python auto_rename_mkv_chapters.py video.mkv --template "♪ {name} - {artist_first}"

# 查看所有预设模板
python auto_rename_mkv_chapters.py --list-templates

# 查看可用变量
python auto_rename_mkv_chapters.py --show-variables
```

| 参数 | 说明 | 示例 |
|------|------|------|
| `--template` | 预设模板名称或自定义格式 | `--template simple` |
| `--list-templates` | 列出所有预设模板 | - |
| `--show-variables` | 显示可用的模板变量 | - |

#### 4. 配置文件参数

```bash
# 使用配置文件
python auto_rename_mkv_chapters.py --config config.json

# 配置文件 + 命令行覆盖
python auto_rename_mkv_chapters.py --config config.json video.mkv --template full

# 创建配置文件模板
python auto_rename_mkv_chapters.py --create-config my_config.json
```

| 参数 | 说明 | 示例 |
|------|------|------|
| `--config` | 配置文件路径 | `--config config.json` |
| `--create-config` | 创建默认配置文件 | `--create-config config.json` |

#### 5. 工具路径参数

```bash
# 指定工具路径（如果自动检测失败）
python auto_rename_mkv_chapters.py video.mkv \
    --ffmpeg "C:/Program Files/ffmpeg/bin/ffmpeg.exe" \
    --mkvextract "C:/Program Files/MKVToolNix/mkvextract.exe" \
    --mkvpropedit "C:/Program Files/MKVToolNix/mkvpropedit.exe"
```

| 参数 | 说明 | 示例 |
|------|------|------|
| `--ffmpeg` | FFmpeg可执行文件路径 | `--ffmpeg path/to/ffmpeg.exe` |
| `--mkvextract` | mkvextract可执行文件路径 | `--mkvextract path/to/mkvextract.exe` |
| `--mkvpropedit` | mkvpropedit可执行文件路径 | `--mkvpropedit path/to/mkvpropedit.exe` |

#### 6. 其他选项参数

```bash
# 禁用自动备份
python auto_rename_mkv_chapters.py video.mkv --no-backup

# 跳过工具依赖检查
python auto_rename_mkv_chapters.py video.mkv --skip-check

# 从备份还原章节
python auto_rename_mkv_chapters.py video.mkv --restore

# 指定备份文件还原
python auto_rename_mkv_chapters.py video.mkv --restore --backup-file custom.json
```

| 参数 | 说明 | 示例 |
|------|------|------|
| `--no-backup` | 不备份原始章节信息 | `--no-backup` |
| `--skip-check` | 跳过依赖工具检查 | `--skip-check` |
| `--restore` | 从备份还原章节信息 | `--restore` |
| `--backup-file` | 指定备份文件路径 | `--backup-file backup.json` |

### 常用命令组合

#### 快速处理

```bash
# 默认设置处理
python auto_rename_mkv_chapters.py video.mkv

# 简洁模板 + 中间采样
python auto_rename_mkv_chapters.py video.mkv --template simple --strategy middle

# 完整模板 + 跳过10秒
python auto_rename_mkv_chapters.py video.mkv --template full --offset 10
```

#### 高级用法

```bash
# 自定义模板 + 自定义位置
python auto_rename_mkv_chapters.py video.mkv \
    --template "{name} by {artist_first}" \
    --strategy custom --percentage 0.3

# 不备份 + 跳过检查（快速模式）
python auto_rename_mkv_chapters.py video.mkv --no-backup --skip-check

# 指定输出 + 中间采样 + 5秒采样
python auto_rename_mkv_chapters.py video.mkv -o output.mkv \
    --strategy middle --duration 5
```

#### 批量处理

```bash
# PowerShell批量处理
Get-ChildItem *.mkv | ForEach-Object {
    python auto_rename_mkv_chapters.py $_.FullName --template simple --strategy middle
}

# Bash批量处理
for file in *.mkv; do
    python auto_rename_mkv_chapters.py "$file" --template simple --strategy middle
done
```

---

## 🎯 功能详解

### 1. 章节模板系统

#### 预设模板对比

| 模板名 | 格式 | 示例 | 适用场景 |
|--------|------|------|----------|
| default | `{name} - {artists}` | ハジメテノオト - 初音ミク, malo | 通用场景 |
| simple | `{name}` | ハジメテノオト | 简洁显示 |
| with_trans | `{name}（{trans_name}）- {artists}` | ハジメテノオト（初次之音）- 初音ミク | 需要译名 |
| full | `{name} - {artists} [{album}]` | ハジメテノオト - 初音ミク [VOCALOID] | 完整信息 |
| artist_first | `{artists} - {name}` | 初音ミク - ハジメテノオト | 歌手优先 |
| japanese | `{name} / {artists}` | ハジメテノオト / 初音ミク | 日式风格 |

#### 自定义模板示例

```bash
# 音符前缀
--template "♪ {name} - {artists}"
# 输出: ♪ ハジメテノオト - 初音ミク

# 只显示第一个歌手
--template "{name} by {artist_first}"
# 输出: ハジメテノオト by 初音ミク

# 带专辑和热度
--template "{name} [{album}] ♡{popularity}"
# 输出: ハジメテノオト [VOCALOID] ♡85

# 完全自定义
--template "🎵 {artist_first} - {name} (ID: {id})"
# 输出: 🎵 初音ミク - ハジメテノオト (ID: 123456)
```

### 2. 识别策略系统

#### 策略选择指南

| 视频类型 | 推荐策略 | 理由 |
|----------|----------|------|
| 音乐会录像 | middle | 避开前奏和尾奏，主歌部分特征明显 |
| MV合集 | start + offset | 跳过片头，从主歌开始 |
| 纯音乐合集 | middle | 中间部分最稳定 |
| 现场演出 | custom 0.3 | 30%位置通常是主歌部分 |
| 短视频合集 | start + 小offset | 视频短，快速进入主题 |

#### 策略参数调优

**START策略**：
```bash
# 短前奏（3秒）
--strategy start --offset 3

# 标准前奏（5秒，默认）
--strategy start --offset 5

# 长前奏（10秒）
--strategy start --offset 10
```

**CUSTOM策略**：
```bash
# 前1/4位置
--strategy custom --percentage 0.25

# 中间位置
--strategy custom --percentage 0.5

# 后1/3位置
--strategy custom --percentage 0.67
```

**采样时长**：
```bash
# 短采样（快速识别）
--duration 3

# 标准采样
--duration 4

# 长采样（提高准确度）
--duration 5
```

### 3. 备份与还原

#### 自动备份

脚本会自动创建 `.chapters.backup.json` 备份文件：

```bash
# 处理视频（自动备份）
python auto_rename_mkv_chapters.py video.mkv
# 生成: video.chapters.backup.json

# 禁用备份
python auto_rename_mkv_chapters.py video.mkv --no-backup
```

#### 还原章节

```bash
# 从默认备份还原
python auto_rename_mkv_chapters.py video.mkv --restore

# 从指定备份还原
python auto_rename_mkv_chapters.py video.mkv --restore --backup-file my_backup.json
```

#### 备份文件格式

```json
[
  {
    "uid": "1",
    "start_time": "00:00:00.000000000",
    "end_time": "00:02:30.483000000",
    "title": "01.ハジメテノオト / malo"
  }
]
```

### 4. 工具依赖

#### 必需工具

- **FFmpeg** - 音频提取
- **MKVToolNix** (mkvextract, mkvpropedit) - 章节操作

#### 自动检测

脚本会自动检测以下位置的工具：
- Windows: `C:\Program Files\`, 系统PATH
- Linux/Mac: `/usr/bin/`, `/usr/local/bin/`

#### 手动指定

```bash
python auto_rename_mkv_chapters.py video.mkv \
    --ffmpeg "C:/custom/path/ffmpeg.exe" \
    --mkvextract "C:/custom/path/mkvextract.exe" \
    --mkvpropedit "C:/custom/path/mkvpropedit.exe"
```

---

## 📚 完整示例

### 示例1: 音乐会视频处理

**场景**: 处理一个音乐会录像，包含45首歌曲章节

**方式A - 命令行**：
```bash
python auto_rename_mkv_chapters.py concert.mkv \
    --template full \
    --strategy middle \
    --duration 5 \
    -o concert_renamed.mkv
```

**方式B - 配置文件**：

创建 `concert_config.json`：
```json
{
  "mkv_file": "concert.mkv",
  "output": "concert_renamed.mkv",
  "template": "full",
  "recognition": {
    "strategy": "middle",
    "duration": 5
  }
}
```

执行：
```bash
python auto_rename_mkv_chapters.py --config concert_config.json
```

### 示例2: MV合集批量处理

**场景**: 批量处理多个MV合集文件

**配置文件** (`mv_batch.json`)：
```json
{
  "template": "simple",
  "recognition": {
    "strategy": "start",
    "offset": 10.0,
    "duration": 4
  },
  "options": {
    "no_backup": false
  }
}
```

**批处理脚本** (PowerShell)：
```powershell
Get-ChildItem D:\Videos\MV\*.mkv | ForEach-Object {
    Write-Host "处理: $($_.Name)" -ForegroundColor Green
    python auto_rename_mkv_chapters.py --config mv_batch.json $_.FullName
}
```

### 示例3: 测试不同模板

**场景**: 在同一个视频上测试不同模板效果

```bash
# 1. 测试simple模板
python auto_rename_mkv_chapters.py test.mkv --template simple

# 2. 查看效果，不满意则还原
python auto_rename_mkv_chapters.py test.mkv --restore

# 3. 测试with_trans模板
python auto_rename_mkv_chapters.py test.mkv --template with_trans

# 4. 再次还原
python auto_rename_mkv_chapters.py test.mkv --restore

# 5. 最终选择full模板
python auto_rename_mkv_chapters.py test.mkv --template full
```

### 示例4: 自定义格式

**场景**: 使用自定义格式，符合个人喜好

**命令行方式**：
```bash
python auto_rename_mkv_chapters.py video.mkv \
    --template "🎵 {name} by {artist_first}" \
    --strategy middle
```

**配置文件方式** (`custom_format.json`)：
```json
{
  "custom_template": "🎵 {name} by {artist_first}",
  "recognition": {
    "strategy": "middle"
  }
}
```

### 示例5: 混合使用

**场景**: 使用配置文件作为基础，命令行覆盖特定参数

**基础配置** (`base.json`)：
```json
{
  "template": "default",
  "recognition": {
    "strategy": "middle",
    "duration": 3
  }
}
```

**不同场景使用**：
```bash
# 场景A: 使用simple模板（覆盖配置文件）
python auto_rename_mkv_chapters.py --config base.json video1.mkv --template simple

# 场景B: 使用start策略（覆盖配置文件）
python auto_rename_mkv_chapters.py --config base.json video2.mkv --strategy start --offset 8

# 场景C: 不备份（覆盖配置文件）
python auto_rename_mkv_chapters.py --config base.json video3.mkv --no-backup
```

---

## 🎓 最佳实践

### 1. 配置文件管理

```
project/
├── configs/
│   ├── default.json      # 默认配置
│   ├── concert.json      # 音乐会配置
│   ├── mv.json          # MV配置
│   └── batch.json       # 批处理配置
└── videos/
    ├── concert1.mkv
    └── concert2.mkv
```

### 2. 选择使用方式

| 场景 | 推荐方式 | 原因 |
|------|----------|------|
| 单个文件快速处理 | 命令行参数 | 快速灵活 |
| 批量处理 | 配置文件 | 统一标准 |
| 复杂配置 | 配置文件 + 命令行 | 灵活组合 |
| 团队协作 | 配置文件 | 易于共享 |
| 测试调优 | 命令行参数 | 快速试错 |

### 3. 工作流程建议

```bash
# 1. 创建配置模板
python auto_rename_mkv_chapters.py --create-config my_config.json

# 2. 编辑配置文件（根据需求调整）

# 3. 在测试文件上验证
python auto_rename_mkv_chapters.py --config my_config.json test.mkv

# 4. 检查效果

# 5. 如不满意，还原并调整
python auto_rename_mkv_chapters.py test.mkv --restore

# 6. 确认配置后批量处理
Get-ChildItem *.mkv | ForEach-Object {
    python auto_rename_mkv_chapters.py --config my_config.json $_.FullName
}
```

### 4. 常见问题解决

#### 识别率低？

```bash
# 尝试调整采样策略
--strategy middle           # 换到中间
--strategy start --offset 8  # 增加偏移
--duration 5                # 增加采样时长
```

#### 工具未找到？

```bash
# 手动指定工具路径
--ffmpeg "C:/path/to/ffmpeg.exe"
--mkvextract "C:/path/to/mkvextract.exe"
--mkvpropedit "C:/path/to/mkvpropedit.exe"
```

#### 章节格式不满意？

```bash
# 查看所有模板
python auto_rename_mkv_chapters.py --list-templates

# 查看可用变量
python auto_rename_mkv_chapters.py --show-variables

# 使用自定义模板
--template "{name} by {artist_first}"
```

---

## 📊 功能速查表

### 配置文件 vs 命令行参数

| 功能 | 配置文件键名 | 命令行参数 | 优先级 |
|------|------------|-----------|--------|
| 输入文件 | `mkv_file` | `mkv_file` (位置参数) | 命令行 |
| 输出文件 | `output` | `-o, --output` | 命令行 |
| 章节模板 | `template` | `--template` | 命令行 |
| 自定义模板 | `custom_template` | `--template "..."` | 命令行 |
| 采样策略 | `recognition.strategy` | `--strategy` | 命令行 |
| 延迟秒数 | `recognition.offset` | `--offset` | 命令行 |
| 位置百分比 | `recognition.percentage` | `--percentage` | 命令行 |
| 采样时长 | `recognition.duration` | `--duration` | 命令行 |
| FFmpeg路径 | `tools.ffmpeg` | `--ffmpeg` | 命令行 |
| mkvextract路径 | `tools.mkvextract` | `--mkvextract` | 命令行 |
| mkvpropedit路径 | `tools.mkvpropedit` | `--mkvpropedit` | 命令行 |
| 禁用备份 | `options.no_backup` | `--no-backup` | 命令行 |
| 跳过检查 | `options.skip_check` | `--skip-check` | 命令行 |

### 快速命令参考

```bash
# 帮助和信息
--help                    # 显示帮助
--list-templates          # 列出所有模板
--show-variables          # 显示模板变量
--create-config FILE      # 创建配置文件

# 基本处理
video.mkv                            # 使用默认设置
video.mkv -o output.mkv              # 指定输出
video.mkv --template simple          # 使用预设模板
video.mkv --template "{name}"        # 自定义模板

# 识别策略
--strategy start --offset 5          # 从开始+5秒
--strategy middle                    # 从中间
--strategy end                       # 从末尾
--strategy custom --percentage 0.3   # 从30%位置
--duration 5                         # 采样5秒

# 配置文件
--config config.json                 # 使用配置文件
--config config.json video.mkv       # 配置+命令行

# 备份还原
--restore                            # 还原章节
--restore --backup-file file.json    # 从指定备份还原
--no-backup                          # 不备份

# 其他
--skip-check                         # 跳过工具检查
--ffmpeg PATH                        # 指定FFmpeg路径
```

---

## 💡 提示

1. **首次使用**建议先在测试文件上运行，确认效果
2. **批量处理**前建议使用配置文件，便于管理
3. **测试模板**时可以利用 `--restore` 快速还原
4. **配置文件**可以纳入版本控制，方便团队协作
5. **命令行参数**始终优先于配置文件，便于临时调整

---

## ⚖️ 优先级规则总结

```
命令行参数 > 配置文件 > 默认值
```

**示例**：
- 配置文件设置: `"template": "simple"`
- 命令行参数: `--template full`
- **实际使用**: `full` ✅

这个设计让你可以：
- 用配置文件设置常用默认值
- 用命令行参数临时覆盖特定选项
- 灵活适应不同场景

---

## 📞 获取帮助

```bash
# 显示完整帮助
python auto_rename_mkv_chapters.py --help

# 查看版本信息
python auto_rename_mkv_chapters.py --version
```
