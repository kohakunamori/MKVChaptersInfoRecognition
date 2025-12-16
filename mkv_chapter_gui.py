import sys
import os
import asyncio
import json
import subprocess
import io
import contextlib
import traceback
from pathlib import Path
from typing import List, Optional

# Ensure we can import the local module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                   QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                                   QTableWidget, QTableWidgetItem, QSlider, QStyle,
                                   QMessageBox, QGroupBox, QFormLayout, QComboBox,
                                   QDoubleSpinBox, QSpinBox, QHeaderView, QSplitter,
                                   QProgressDialog, QLineEdit, QDialog, QDialogButtonBox,
                                   QTextEdit, QMenu)
    from PySide6.QtCore import Qt, QUrl, QThread, Signal, QTime, QTimer, QSize
    from PySide6.QtGui import QAction, QIcon, QColor, QBrush, QFont
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QVideoWidget
except ImportError:
    print("错误: 未安装 PySide6 库。请运行: pip install PySide6")
    sys.exit(1)

# Import core logic from the existing script
try:
    from auto_rename_mkv_chapters import (MKVChapterManager, ChapterTemplate, 
                                          RecognitionConfig, SamplingStrategy,
                                          find_tool_path, MKVChapter, check_dependencies)
except ImportError as e:
    print(f"错误: 无法导入核心模块: {e}")
    sys.exit(1)

# ==========================================
# Styles & Themes
# ==========================================

DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #2b2b2b;
    color: #ffffff;
}
QWidget {
    color: #ffffff;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 14px;
}
QGroupBox {
    border: 1px solid #555;
    border-radius: 5px;
    margin-top: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #aaa;
}
QPushButton {
    background-color: #3d3d3d;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 5px 15px;
    min-height: 25px;
    color: #ffffff;
}
QPushButton:hover {
    background-color: #4d4d4d;
    border-color: #666;
}
QPushButton:pressed {
    background-color: #2d2d2d;
}
QPushButton:disabled {
    background-color: #2b2b2b;
    color: #666;
    border-color: #444;
}
QPushButton#PrimaryButton {
    background-color: #0078d4;
    border-color: #0078d4;
    color: #ffffff;
}
QPushButton#PrimaryButton:hover {
    background-color: #1084d9;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #3d3d3d;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px;
    color: #ffffff;
}
QComboBox QAbstractItemView {
    background-color: #3d3d3d;
    color: #ffffff;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    border: 1px solid #555;
}
QTableWidget {
    background-color: #333;
    gridline-color: #444;
    border: 1px solid #555;
    color: #ffffff;
}
QTableWidget::item {
    padding: 5px;
}
QTableWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #2d2d2d;
    padding: 5px;
    border: 1px solid #444;
    color: #ffffff;
}
QSlider::groove:horizontal {
    border: 1px solid #444;
    height: 6px;
    background: #333;
    margin: 2px 0;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #0078d4;
    border: 1px solid #0078d4;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QScrollBar:vertical {
    border: none;
    background: #2b2b2b;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #555;
    min-height: 20px;
    border-radius: 5px;
}
QTextEdit {
    background-color: #2b2b2b;
    color: #ffffff;
    border: 1px solid #555;
}
"""

# ==========================================
# Worker Threads
# ==========================================

class RecognitionWorker(QThread):
    """Background worker for recognizing songs"""
    progress = Signal(int, int)  # current, total
    chapter_result = Signal(int, object, str)  # index, song_info, new_title
    finished_all = Signal()
    error_occurred = Signal(str)
    log_message = Signal(str)

    def __init__(self, mkv_file, chapters, config, template, tools):
        super().__init__()
        self.mkv_file = mkv_file
        self.chapters = chapters
        self.config = config
        self.template = template
        self.tools = tools
        self.is_running = True

    def run(self):
        try:
            self.log_message.emit("正在初始化识别引擎...")
            
            total = len(self.chapters)
            for i, chapter in enumerate(self.chapters):
                if not self.is_running:
                    self.log_message.emit("⚠️ 任务已取消")
                    break
                
                self.log_message.emit(f"正在分析第 {i+1}/{total} 章: {chapter.title}")
                
                # Calculate sample time
                start_seconds = MKVChapter.parse_time_to_seconds(chapter.start_time)
                end_seconds = MKVChapter.parse_time_to_seconds(chapter.end_time) if chapter.end_time else None
                
                sample_start = self.config.calculate_sample_time(
                    start_seconds, end_seconds
                )
                
                # Call subprocess for recognition
                if getattr(sys, 'frozen', False):
                    # Running as compiled exe
                    # Assume recognition_worker.exe is in the same directory as the executable
                    worker_exe = os.path.join(os.path.dirname(sys.executable), 'recognition_worker.exe')
                    cmd = [
                        worker_exe,
                        '--mkv', self.mkv_file,
                        '--start', str(sample_start),
                        '--duration', str(self.config.duration),
                        '--ffmpeg', self.tools.get('ffmpeg', 'ffmpeg')
                    ]
                else:
                    cmd = [
                        sys.executable,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recognition_worker.py'),
                        '--mkv', self.mkv_file,
                        '--start', str(sample_start),
                        '--duration', str(self.config.duration),
                        '--ffmpeg', self.tools.get('ffmpeg', 'ffmpeg')
                    ]
                
                # Hide window on Windows
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                # Add timeout to prevent hanging
                try:
                    process = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', 
                                           startupinfo=startupinfo, timeout=30)
                except subprocess.TimeoutExpired:
                    self.log_message.emit(f"❌ 识别超时 (30s) - 可能原因: 网络请求阻塞或系统资源不足")
                    self.chapter_result.emit(i, None, "")
                    self.progress.emit(i + 1, total)
                    continue
                
                if process.returncode == 0:
                    try:
                        result = json.loads(process.stdout)
                        if result.get('success'):
                            song_info = result.get('data')
                            new_title = self.template.format(song_info)
                            
                            # Check for consecutive duplicate results
                            if i > 0 and hasattr(self, 'last_result_title') and self.last_result_title == new_title:
                                self.log_message.emit(f"⚠️ 警告: 第 {i+1} 章识别结果与上一章完全相同 ({new_title})。可能原因: 采样位置处于两首歌之间，或视频定位不准确。建议调整采样偏移量。")
                            
                            self.last_result_title = new_title
                            self.chapter_result.emit(i, song_info, new_title)
                            self.log_message.emit(f"✅ 识别成功: {new_title}")
                        else:
                            self.chapter_result.emit(i, None, "")
                            error_msg = result.get('error', '未知错误')
                            tip = ""
                            if "No match found" in error_msg:
                                tip = " (可能原因: 歌曲未收录、片段杂音过多或太短)"
                            self.log_message.emit(f"⚠️ 未识别到歌曲: {error_msg}{tip}")
                    except json.JSONDecodeError:
                        self.log_message.emit(f"❌ 解析结果失败: {process.stdout} (可能原因: 脚本输出格式错误)")
                else:
                    self.log_message.emit(f"❌ 识别进程错误: {process.stderr} (可能原因: 依赖缺失或环境问题)")
                
                self.progress.emit(i + 1, total)
            
            if self.is_running:
                self.finished_all.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            import traceback
            traceback.print_exc()

    def stop(self):
        self.is_running = False

# ==========================================
# Dialogs
# ==========================================

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_config=None, current_template=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(500, 400)
        self.layout = QVBoxLayout(self)
        
        # Template Settings
        template_group = QGroupBox("章节模板")
        template_layout = QFormLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "default", "simple", "with_trans", "full", 
            "artist_first", "minimal", "with_id", "detailed", "japanese"
        ])
        self.template_combo.currentTextChanged.connect(self.on_template_change)
        
        self.custom_template_edit = QLineEdit()
        self.custom_template_edit.setPlaceholderText("自定义模板，例如: {name} by {artists}")
        
        # Help text
        help_text = "支持变量: {name}, {trans_name}, {artists}, {artist_first}, {album}, {id}, {popularity}"
        help_label = QLabel(help_text)
        help_label.setStyleSheet("color: #aaa; font-size: 11px;")
        help_label.setWordWrap(True)
        
        template_layout.addRow("预设模板:", self.template_combo)
        template_layout.addRow("自定义模板:", self.custom_template_edit)
        template_layout.addRow("", help_label)
        template_group.setLayout(template_layout)
        self.layout.addWidget(template_group)
        
        # Strategy Settings
        strategy_group = QGroupBox("识别策略")
        self.strategy_layout = QFormLayout()
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["start", "middle", "end", "custom"])
        self.strategy_combo.currentTextChanged.connect(self.on_strategy_change)
        
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(0, 60)
        self.offset_spin.setValue(5.0)
        self.offset_spin.setSuffix(" 秒")
        
        self.percentage_spin = QDoubleSpinBox()
        self.percentage_spin.setRange(0, 1.0)
        self.percentage_spin.setSingleStep(0.1)
        self.percentage_spin.setValue(0.5)
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 10)
        self.duration_spin.setValue(3)
        self.duration_spin.setSuffix(" 秒")
        
        self.strategy_layout.addRow("采样策略:", self.strategy_combo)
        self.strategy_layout.addRow("起始偏移 (Start):", self.offset_spin)
        self.strategy_layout.addRow("位置百分比 (Custom):", self.percentage_spin)
        self.strategy_layout.addRow("采样时长:", self.duration_spin)
        strategy_group.setLayout(self.strategy_layout)
        self.layout.addWidget(strategy_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)
        
        # Load current values
        if current_config:
            self.strategy_combo.setCurrentText(current_config.strategy.value)
            self.offset_spin.setValue(current_config.offset)
            self.percentage_spin.setValue(current_config.percentage)
            self.duration_spin.setValue(current_config.duration)
            
        if current_template:
            if current_template.template in ["{name} - {artists}", "{name}", "{name}（{trans_name}）- {artists}"]:
                # Try to match preset (simplified logic)
                pass
            # Just set custom if it looks custom, otherwise default
            self.custom_template_edit.setText(current_template.template)
            
        self.on_strategy_change(self.strategy_combo.currentText())

    def on_template_change(self, text):
        # Update custom edit with preset value
        t = ChapterTemplate(text)
        self.custom_template_edit.setText(t.template)

    def on_strategy_change(self, text):
        is_start = (text == "start")
        is_custom = (text == "custom")
        self.strategy_layout.setRowVisible(self.offset_spin, is_start)
        self.strategy_layout.setRowVisible(self.percentage_spin, is_custom)

    def get_config(self):
        return RecognitionConfig(
            strategy=SamplingStrategy(self.strategy_combo.currentText()),
            offset=self.offset_spin.value(),
            percentage=self.percentage_spin.value(),
            duration=self.duration_spin.value()
        )

    def get_template(self):
        return self.custom_template_edit.text()

# ==========================================
# Main Window
# ==========================================

class MKVChapterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MKV 章节自动识别工具 - 网易云API")
        self.resize(1200, 800)
        
        # State
        self.mkv_file = None
        self.chapters = []
        self.tools = {}
        self.config = RecognitionConfig(strategy=SamplingStrategy.START, offset=5.0, percentage=0.5, duration=3)
        self.template = ChapterTemplate("default")
        self.player_duration = 0
        
        # Initialize UI
        self.init_ui()
        self.check_tools()

    def init_ui(self):
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top Bar
        top_bar = QHBoxLayout()
        
        self.btn_open = QPushButton("📂 打开 MKV 文件")
        self.btn_open.clicked.connect(self.open_file)
        self.btn_open.setObjectName("PrimaryButton")
        
        self.btn_settings = QPushButton("⚙️ 设置")
        self.btn_settings.clicked.connect(self.open_settings)
        
        self.btn_save = QPushButton("💾 保存到文件")
        self.btn_save.clicked.connect(self.save_chapters)
        self.btn_save.setEnabled(False)
        
        self.btn_backup = QPushButton("📥 备份当前状态")
        self.btn_backup.clicked.connect(self.backup_current_state)
        self.btn_backup.setEnabled(False)
        
        self.btn_restore = QPushButton("Hz 还原备份")
        self.btn_restore.clicked.connect(self.restore_backup)
        self.btn_restore.setEnabled(False)
        
        top_bar.addWidget(self.btn_open)
        top_bar.addWidget(self.btn_settings)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_backup)
        top_bar.addWidget(self.btn_restore)
        top_bar.addWidget(self.btn_save)
        
        main_layout.addLayout(top_bar)
        
        # Splitter (Video | Table)
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel: Video Player
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(400, 300)
        self.video_widget.setStyleSheet("background-color: black;")
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.btn_seek_back = QPushButton("<<")
        self.btn_seek_back.setFixedWidth(30)
        self.btn_seek_back.setToolTip("后退 0.5 秒 (键盘 ←)")
        self.btn_seek_back.clicked.connect(self.seek_backward)
        
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedWidth(40)
        self.btn_play.setToolTip("播放/暂停 (空格)")
        self.btn_play.clicked.connect(self.toggle_play)
        
        self.btn_seek_fwd = QPushButton(">>")
        self.btn_seek_fwd.setFixedWidth(30)
        self.btn_seek_fwd.setToolTip("前进 0.5 秒 (键盘 →)")
        self.btn_seek_fwd.clicked.connect(self.seek_forward)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        
        self.lbl_time = QLabel("00:00 / 00:00")
        
        # Volume
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setToolTip("音量 (键盘 ↑/↓)")
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        controls_layout.addWidget(self.btn_seek_back)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_seek_fwd)
        controls_layout.addWidget(self.slider)
        controls_layout.addWidget(self.lbl_time)
        controls_layout.addWidget(QLabel(" 🔊 "))
        controls_layout.addWidget(self.volume_slider)
        
        left_layout.addWidget(self.video_widget)
        left_layout.addLayout(controls_layout)
        
        # Right Panel: Chapter Table
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["时间", "原始标题", "识别结果 (可编辑)", "状态"])
        # Allow manual resizing
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 250)
        self.table.setColumnWidth(2, 250)
        self.table.setColumnWidth(3, 80)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellClicked.connect(self.on_table_click)
        
        right_layout.addWidget(self.table)
        
        # Action Bar below table
        action_bar = QHBoxLayout()
        self.btn_recognize_all = QPushButton("🎵 识别所有章节")
        self.btn_recognize_all.clicked.connect(self.start_recognition)
        self.btn_recognize_all.setEnabled(False)
        self.btn_recognize_all.setObjectName("PrimaryButton")
        
        action_bar.addWidget(self.btn_recognize_all)
        right_layout.addLayout(action_bar)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 2)
        
        # Vertical Splitter for Main Content and Logs
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(splitter)
        
        # Log Area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        v_splitter.addWidget(self.log_area)
        v_splitter.setStretchFactor(0, 4)
        v_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(v_splitter)

    def log(self, message):
        self.log_area.append(message)
        # Scroll to bottom
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def check_tools(self):
        self.log("正在检查依赖工具...")
        
        # Capture stdout to show in log
        f = io.StringIO()
        tools = None
        try:
            with contextlib.redirect_stdout(f):
                tools = check_dependencies()
        except Exception as e:
            self.log(f"❌ 检查工具时发生错误: {e}")
        
        # Log the captured output
        output = f.getvalue()
        for line in output.splitlines():
            if line.strip():
                self.log(line)
                
        if tools:
            self.tools = tools
        else:
            QMessageBox.critical(self, "错误", "缺少必要工具，请查看日志窗口获取详细信息。\n\n请确保安装了 FFmpeg 和 MKVToolNix。")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "打开 MKV 文件", "", "MKV Files (*.mkv)")
        if file_path:
            self.mkv_file = file_path
            self.load_mkv()

    def load_mkv(self):
        self.log(f"正在加载: {self.mkv_file}")
        self.player.setSource(QUrl.fromLocalFile(self.mkv_file))
        self.player.play()
        self.player.pause()
        self.btn_play.setText("▶")
        
        # Load chapters
        try:
            if not self.mkv_file:
                return
            manager = MKVChapterManager(
                str(self.mkv_file), 
                mkvextract_path=str(self.tools.get('mkvextract', 'mkvextract')),
                mkvpropedit_path=str(self.tools.get('mkvpropedit', 'mkvpropedit'))
            )
            self.chapters = manager.extract_chapters()
            self.populate_table()
            self.btn_recognize_all.setEnabled(True)
            self.btn_save.setEnabled(True)
            self.btn_restore.setEnabled(True)
            self.btn_backup.setEnabled(True)
            self.log(f"✅ 加载了 {len(self.chapters)} 个章节")
        except Exception as e:
            self.log(f"❌ 加载章节失败: {e}")
            QMessageBox.warning(self, "错误", f"加载章节失败: {e}")

    def populate_table(self):
        self.table.setRowCount(len(self.chapters))
        for i, chapter in enumerate(self.chapters):
            # Time
            self.table.setItem(i, 0, QTableWidgetItem(chapter.start_time))
            
            # Original Title
            self.table.setItem(i, 1, QTableWidgetItem(chapter.title))
            
            # Recognized Title (Editable)
            item_rec = QTableWidgetItem("")
            self.table.setItem(i, 2, item_rec)
            
            # Status
            self.table.setItem(i, 3, QTableWidgetItem("待处理"))

    def on_table_click(self, row, col):
        # Seek video to chapter start
        time_str = self.table.item(row, 0).text()
        # Parse time string (00:00:00.000) to milliseconds
        try:
            parts = time_str.split(':')
            h = int(parts[0])
            m = int(parts[1])
            s = float(parts[2])
            ms = int((h * 3600 + m * 60 + s) * 1000)
            self.player.setPosition(ms)
            self.player.play()
            self.btn_play.setText("⏸")
        except:
            pass

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.btn_play.setText("▶")
        else:
            self.player.play()
            self.btn_play.setText("⏸")

    def on_position_changed(self, position):
        self.slider.setValue(position)
        self.update_time_label()

    def on_duration_changed(self, duration):
        self.player_duration = duration
        self.slider.setRange(0, duration)
        self.update_time_label()

    def set_position(self, position):
        self.player.setPosition(position)

    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100.0)

    def update_time_label(self):
        def fmt(ms):
            s = ms // 1000
            m = s // 60
            s = s % 60
            return f"{m:02d}:{s:02d}"
        
        current = fmt(self.player.position())
        total = fmt(self.player_duration)
        self.lbl_time.setText(f"{current} / {total}")

    def seek_backward(self):
        """Rewind 0.5 seconds"""
        self.player.setPosition(max(0, self.player.position() - 500))

    def seek_forward(self):
        """Fast forward 0.5 seconds"""
        self.player.setPosition(min(self.player_duration, self.player.position() + 500))

    def volume_up(self):
        self.volume_slider.setValue(min(100, self.volume_slider.value() + 5))

    def volume_down(self):
        self.volume_slider.setValue(max(0, self.volume_slider.value() - 5))

    def keyPressEvent(self, event):
        # Handle keyboard shortcuts
        # Note: If a widget like QTableWidget has focus, it might consume arrow keys first.
        if event.key() == Qt.Key_Left:
            self.seek_backward()
        elif event.key() == Qt.Key_Right:
            self.seek_forward()
        elif event.key() == Qt.Key_Up:
            self.volume_up()
        elif event.key() == Qt.Key_Down:
            self.volume_down()
        elif event.key() == Qt.Key_Space:
            self.toggle_play()
        else:
            super().keyPressEvent(event)

    def open_settings(self):
        dialog = SettingsDialog(self, self.config, self.template)
        if dialog.exec():
            self.config = dialog.get_config()
            tpl_str = dialog.get_template()
            self.template = ChapterTemplate("default")
            self.template.set_custom_template(tpl_str)
            self.log("✅ 设置已更新")

    def start_recognition(self):
        if not self.chapters:
            return
        
        # Create progress dialog
        self.progress_bar = QProgressDialog("正在识别...", "取消", 0, len(self.chapters), self)
        self.progress_bar.setWindowTitle("处理进度")
        self.progress_bar.setWindowModality(Qt.WindowModal)
        self.progress_bar.setMinimumDuration(0)
        self.progress_bar.canceled.connect(self.cancel_recognition)
        self.progress_bar.show()
        
        self.worker = RecognitionWorker(self.mkv_file, self.chapters, self.config, self.template, self.tools)
        self.worker.progress.connect(self.update_progress)
        self.worker.chapter_result.connect(self.update_chapter_result)
        self.worker.log_message.connect(self.log)
        self.worker.finished_all.connect(self.recognition_finished)
        self.worker.error_occurred.connect(self.on_worker_error)
        
        self.worker.start()

    def cancel_recognition(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            self.log("⚠️ 用户取消了任务")

    def recognize_single(self, index):
        # Create a temporary worker for single chapter
        chapter = self.chapters[index]
        self.log(f"正在单独识别第 {index+1} 章...")
        
        # Reuse worker logic but for one item
        # For simplicity, we just run the worker for a list of 1 item, 
        # but we need to handle the index mapping. 
        # Actually, let's just run the full worker but modify it to support single index?
        # Or just run it for one item list and map back.
        pass # TODO: Implement single recognition if needed, for now "Recognize All" is main feature

    def update_progress(self, current, total):
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.setValue(current)

    def update_chapter_result(self, index, song_info, new_title):
        if new_title:
            self.table.item(index, 2).setText(new_title)
            self.table.item(index, 3).setText("✅ 成功")
            self.table.item(index, 3).setForeground(QBrush(QColor("#00ff00")))
        else:
            self.table.item(index, 3).setText("❌ 失败")
            self.table.item(index, 3).setForeground(QBrush(QColor("#ff0000")))

    def recognition_finished(self):
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.close()
        self.log("🎉 所有识别任务完成")
        QMessageBox.information(self, "完成", "识别完成，请检查结果并保存")

    def on_worker_error(self, error_msg):
        self.log(f"❌ 发生严重错误: {error_msg}")
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.close()
        QMessageBox.critical(self, "错误", f"识别过程中发生错误:\n{error_msg}")

    def save_chapters(self):
        if not self.mkv_file:
            return
            
        # Gather chapters from table
        new_chapters = []
        for i in range(self.table.rowCount()):
            original_chapter = self.chapters[i]
            new_title = self.table.item(i, 2).text()
            
            # Use new title if available, else keep original
            final_title = new_title if new_title.strip() else original_chapter.title
            
            new_chapter = MKVChapter(
                uid=original_chapter.uid,
                start_time=original_chapter.start_time,
                end_time=original_chapter.end_time,
                title=final_title
            )
            new_chapters.append(new_chapter)
            
        # Save
        try:
            manager = MKVChapterManager(
                str(self.mkv_file), 
                mkvextract_path=str(self.tools.get('mkvextract', 'mkvextract')),
                mkvpropedit_path=str(self.tools.get('mkvpropedit', 'mkvpropedit'))
            )
            # Backup first
            # We can reuse the backup logic from the script if we import MKVAutoRename or just implement it here
            # Let's just call update_chapters, assuming user wants to save what they see
            
            manager.update_chapters(new_chapters, str(self.mkv_file))
            self.log(f"💾 章节已保存到文件: {self.mkv_file}")
            QMessageBox.information(self, "成功", f"章节信息已成功保存到文件:\n{self.mkv_file}")
        except Exception as e:
            self.log(f"❌ 保存失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def restore_backup(self):
        if not self.mkv_file:
            return
            
        try:
            from auto_rename_mkv_chapters import MKVAutoRename
            MKVAutoRename.restore_from_backup(
                str(self.mkv_file), 
                mkvpropedit_path=str(self.tools.get('mkvpropedit', 'mkvpropedit'))
            )
            backup_file = Path(self.mkv_file).with_suffix('.chapters.backup.json')
            self.log(f"✅ 已从备份文件还原: {backup_file}")
            self.load_mkv() # Reload
            QMessageBox.information(self, "成功", f"已从以下备份文件还原:\n{backup_file}")
        except Exception as e:
            self.log(f"❌ 还原失败: {e}")
            QMessageBox.warning(self, "错误", f"还原失败: {e}")

    def backup_current_state(self):
        if not self.mkv_file:
            return
            
        try:
            # Re-read chapters from file to ensure we backup what is actually on disk
            manager = MKVChapterManager(
                str(self.mkv_file), 
                mkvextract_path=str(self.tools.get('mkvextract', 'mkvextract')),
                mkvpropedit_path=str(self.tools.get('mkvpropedit', 'mkvpropedit'))
            )
            current_chapters = manager.extract_chapters()
            
            backup_file = Path(self.mkv_file).with_suffix('.chapters.backup.json')
            
            # Check if exists
            if backup_file.exists():
                reply = QMessageBox.question(
                    self, "确认覆盖", 
                    f"备份文件已存在:\n{backup_file}\n\n是否覆盖?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            chapters_data = [
                {
                    'uid': ch.uid,
                    'start_time': ch.start_time,
                    'end_time': ch.end_time,
                    'title': ch.title
                }
                for ch in current_chapters
            ]
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(chapters_data, f, ensure_ascii=False, indent=2)
                
            self.log(f"✅ 已备份当前章节到: {backup_file}")
            QMessageBox.information(self, "成功", f"已创建备份文件:\n{backup_file}")
            
        except Exception as e:
            self.log(f"❌ 备份失败: {e}")
            QMessageBox.critical(self, "错误", f"备份失败: {e}")

if __name__ == "__main__":
    # Global exception handler
    def exception_hook(exctype, value, tb):
        traceback_str = ''.join(traceback.format_exception(exctype, value, tb))
        print(traceback_str) # Print to stderr/stdout
        
        # Ensure we have a QApplication instance
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            
        QMessageBox.critical(None, "发生未捕获的异常", f"程序发生错误:\n{value}\n\n详细信息已打印到控制台。")

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    
    window = MKVChapterGUI()
    window.show()
    
    sys.exit(app.exec())
