# 项目依赖说明

如果您希望直接运行 Python 源代码而不是编译后的 EXE 文件，请按照以下步骤配置环境。

## 1. Python 环境

建议使用 Python 3.10 或更高版本。

### 安装 Python 依赖库

请在终端中运行以下命令安装所需的 Python 库：

```bash
pip install PySide6 pythonmonkey pyncm requests
```

**依赖库说明：**
*   `PySide6`: 用于构建图形用户界面 (GUI)。
*   `pythonmonkey`: 用于在 Python 中运行 JavaScript 代码 (音频指纹生成算法)。
*   `pyncm`: 网易云音乐 API 的 Python 封装。
*   `requests`: 用于网络请求。

## 2. 外部工具

本项目依赖以下外部工具来处理视频和音频文件。请确保它们已安装并添加到系统的 PATH 环境变量中，或者在程序的设置中指定它们的路径。

### FFmpeg
*   **用途**: 用于从 MKV 视频中提取音频片段。
*   **下载**: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
*   **安装**: 下载解压后，将 `bin` 文件夹中的 `ffmpeg.exe` 所在的路径添加到系统环境变量 PATH 中。

### MKVToolNix
*   **用途**: 用于提取和更新 MKV 文件的章节信息 (`mkvextract`, `mkvpropedit`)。
*   **下载**: [https://mkvtoolnix.download/downloads.html](https://mkvtoolnix.download/downloads.html)
*   **安装**: 安装后，确保 `mkvextract.exe` 和 `mkvpropedit.exe` 所在的路径已添加到系统环境变量 PATH 中。

## 3. 运行方式

### 启动 GUI 界面
```bash
python mkv_chapter_gui.py
```

### 仅使用命令行工具
```bash
python auto_rename_mkv_chapters.py --help
```

## 常见问题

*   **pythonmonkey 安装失败**: `pythonmonkey` 需要编译环境。如果在 Windows 上安装失败，请尝试升级 pip (`python -m pip install --upgrade pip`) 或安装 Visual Studio C++ 生成工具。
*   **找不到 ffmpeg/mkvextract**: 请检查是否已将这些工具的路径添加到系统环境变量，或者在 GUI 的设置界面手动指定路径。
