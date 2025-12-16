#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MKV视频章节自动识别与重命名工具
自动识别MKV文件中每个章节的歌曲，并更新章节名称
"""

import os
import sys
import json
import subprocess
import tempfile
import re
import shutil
import platform
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Literal
from datetime import timedelta
# from pythonmonkey import require  # Moved to inside class to avoid import error in GUI
from struct import unpack
import asyncio
from enum import Enum
from dataclasses import dataclass

# 添加ncm-afp目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ncm-afp'))

try:
    from pyncm.apis.track import GetMatchTrackByFP
except ImportError:
    print("错误: 未安装pyncm库，请运行: pip install pyncm")
    sys.exit(1)


def find_tool_path(tool_name: str) -> Optional[str]:
    """查找工具路径，支持Windows自动检测"""
    # 首先检查系统PATH
    tool_path = shutil.which(tool_name)
    if tool_path:
        return tool_path
    
    # Windows特殊处理
    if platform.system() == 'Windows':
        # 常见的MKVToolNix安装路径
        common_paths = [
            r"C:\Program Files\MKVToolNix",
            r"C:\Program Files (x86)\MKVToolNix",
            os.path.expanduser(r"~\AppData\Local\Programs\MKVToolNix"),
        ]
        
        for base_path in common_paths:
            tool_full_path = os.path.join(base_path, f"{tool_name}.exe")
            if os.path.exists(tool_full_path):
                return tool_full_path
        
        # FFmpeg常见路径
        if tool_name == 'ffmpeg':
            ffmpeg_paths = [
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"),
            ]
            for path in ffmpeg_paths:
                if os.path.exists(path):
                    return path
    
    return None


def verify_tool(tool_path: str, tool_name: str) -> Tuple[bool, str]:
    """验证工具是否可用"""
    try:
        # 对于FFmpeg，使用-version而不是--version（两者都支持但返回码不同）
        version_args = ['-version'] if tool_name == 'ffmpeg' else ['--version']
        
        # Windows下隐藏窗口
        startupinfo = None
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(
            [tool_path] + version_args,
            capture_output=True,
            text=True,
            timeout=20,  # 增加超时时间到20秒，防止机械硬盘唤醒或杀毒软件扫描导致超时
            startupinfo=startupinfo
        )
        
        # 检查输出中是否包含版本信息（比返回码更可靠）
        output = result.stdout + result.stderr
        if tool_name in output.lower() or 'version' in output.lower():
            return True, "OK"
        else:
            # 如果返回码是0，即使没匹配到特定字符串也认为是成功的（兼容性）
            if result.returncode == 0:
                return True, "OK"
            return False, f"工具返回错误码: {result.returncode}"
    except subprocess.TimeoutExpired:
        # 超时也尝试认为成功，只要文件存在（可能是系统太卡）
        if os.path.exists(tool_path):
            print(f"⚠️ 警告: 验证 {tool_name} 超时，但文件存在，尝试继续使用。")
            return True, "OK (Timeout)"
        return False, f"验证超时 (20s)"
    except FileNotFoundError:
        return False, f"文件不存在: {tool_path}"
    except Exception as e:
        return False, f"验证失败: {e}"


def check_dependencies():
    """检查所有依赖工具"""
    print("\n🔍 正在检查依赖工具...\n")
    
    tools = {
        'ffmpeg': 'FFmpeg (音频提取)',
        'mkvextract': 'MKVToolNix mkvextract (章节提取)',
        'mkvpropedit': 'MKVToolNix mkvpropedit (章节更新)'
    }
    
    found_tools = {}
    missing_tools = []
    
    for tool_name, description in tools.items():
        print(f"检查 {description}...", end=' ')
        tool_path = find_tool_path(tool_name)
        
        if tool_path:
            is_valid, msg = verify_tool(tool_path, tool_name)
            if is_valid:
                print(f"✅ 找到: {tool_path}")
                found_tools[tool_name] = tool_path
            else:
                print(f"❌ 无效: {msg}")
                missing_tools.append(tool_name)
        else:
            print(f"❌ 未找到")
            missing_tools.append(tool_name)
    
    if missing_tools:
        print(f"\n❌ 缺少以下工具: {', '.join(missing_tools)}")
        print("\n请安装缺失的工具:")
        print("  - FFmpeg: https://ffmpeg.org/download.html")
        print("  - MKVToolNix: https://mkvtoolnix.download/")
        print("\n或使用参数指定工具路径:")
        print("  --ffmpeg 'C:/path/to/ffmpeg.exe'")
        print("  --mkvextract 'C:/Program Files/MKVToolNix/mkvextract.exe'")
        print("  --mkvpropedit 'C:/Program Files/MKVToolNix/mkvpropedit.exe'")
        return None
    
    print("\n✅ 所有依赖工具已就绪\n")
    return found_tools


# ============================================================================
# 章节模板和识别策略配置
# ============================================================================

class SamplingStrategy(Enum):
    """采样策略"""
    START = "start"           # 从章节开始
    MIDDLE = "middle"         # 从章节中间
    END = "end"               # 从章节末尾
    CUSTOM = "custom"         # 自定义位置（百分比）


@dataclass
class RecognitionConfig:
    """识别配置"""
    strategy: SamplingStrategy = SamplingStrategy.START
    offset: float = 5.0                    # 偏移秒数（对START策略）
    percentage: float = 0.5                # 百分比位置（对MIDDLE/CUSTOM策略）
    duration: int = 3                      # 采样时长（秒）
    
    def calculate_sample_time(self, chapter_start: float, chapter_end: Optional[float] = None) -> float:
        """计算采样起始时间"""
        if self.strategy == SamplingStrategy.START:
            return chapter_start + self.offset
        
        elif self.strategy == SamplingStrategy.MIDDLE:
            if chapter_end is None:
                # 如果没有结束时间，假设章节长度为3分钟
                chapter_end = chapter_start + 180
            mid_point = (chapter_start + chapter_end) / 2
            return mid_point - (self.duration / 2)
        
        elif self.strategy == SamplingStrategy.END:
            if chapter_end is None:
                chapter_end = chapter_start + 180
            return max(chapter_start, chapter_end - self.duration - 5)
        
        elif self.strategy == SamplingStrategy.CUSTOM:
            if chapter_end is None:
                chapter_end = chapter_start + 180
            chapter_duration = chapter_end - chapter_start
            return chapter_start + (chapter_duration * self.percentage)
        
        return chapter_start + self.offset


class ChapterTemplate:
    """章节标题模板"""
    
    # 预设模板
    TEMPLATES = {
        'default': '{name} - {artists}',
        'with_trans': '{name}（{trans_name}）- {artists}',
        'full': '{name} - {artists} [{album}]',
        'simple': '{name}',
        'artist_first': '{artists} - {name}',
        'with_id': '{name} - {artists} (ID: {id})',
        'detailed': '{name}（{trans_name}）- {artists} | {album}',
        'japanese': '{name} / {artists}',
        'minimal': '{name} - {artist_first}',
        'custom': None  # 用户自定义
    }
    
    def __init__(self, template: str = 'default'):
        """
        初始化模板
        
        可用变量：
        - {name}: 歌曲名称
        - {trans_name}: 中文译名
        - {artists}: 所有歌手（逗号分隔）
        - {artist_first}: 第一个歌手
        - {album}: 专辑名称
        - {id}: 歌曲ID
        - {popularity}: 热度
        """
        if template in self.TEMPLATES:
            if template == 'custom':
                raise ValueError("请使用 set_custom_template() 设置自定义模板")
            self.template = self.TEMPLATES[template]
        else:
            # 直接使用用户提供的模板字符串
            self.template = template
    
    def set_custom_template(self, template_string: str):
        """设置自定义模板"""
        self.template = template_string
    
    def format(self, song_info: Dict) -> str:
        """格式化章节标题"""
        # 准备模板变量
        variables = {
            'name': song_info.get('name', ''),
            'trans_name': song_info.get('transName', ''),
            'artists': song_info.get('artists', ''),
            'artist_first': song_info.get('artists', '').split(',')[0].strip() if song_info.get('artists') else '',
            'album': song_info.get('album', ''),
            'id': song_info.get('id', ''),
            'popularity': song_info.get('popularity', 0)
        }
        
        # 智能处理译名
        template = self.template
        if '{trans_name}' in template and not variables['trans_name']:
            # 如果模板中有译名但实际没有译名，移除相关部分
            template = re.sub(r'[（(]?\{trans_name\}[）)]?', '', template)
            template = re.sub(r'\s+', ' ', template).strip()
        
        try:
            result = template.format(**variables)
            # 清理多余的空格和标点
            result = re.sub(r'\s*[（(]\s*[）)]\s*', '', result)  # 移除空括号
            result = re.sub(r'\s+', ' ', result).strip()
            result = re.sub(r'\s*-\s*$', '', result)  # 移除末尾的破折号
            return result
        except KeyError as e:
            print(f"  ⚠️  模板变量错误: {e}")
            return song_info.get('name', 'Unknown')
    
    @classmethod
    def list_templates(cls):
        """列出所有预设模板"""
        print("\n可用的预设模板：\n")
        examples = {
            'name': 'ハジメテノオト',
            'trans_name': '初次之音',
            'artists': '初音ミク, malo',
            'artist_first': '初音ミク',
            'album': 'VOCALOID',
            'id': '12345678',
            'popularity': 95
        }
        
        for name, template in cls.TEMPLATES.items():
            if name == 'custom':
                continue
            print(f"  {name}:")
            print(f"    模板: {template}")
            temp = cls(name)
            print(f"    示例: {temp.format(examples)}")
            print()
    
    @classmethod
    def show_available_variables(cls):
        """显示可用的模板变量"""
        print("\n可用的模板变量：\n")
        variables = [
            ('{name}', '歌曲名称', 'ハジメテノオト'),
            ('{trans_name}', '中文译名', '初次之音'),
            ('{artists}', '所有歌手（逗号分隔）', '初音ミク, malo'),
            ('{artist_first}', '第一个歌手', '初音ミク'),
            ('{album}', '专辑名称', 'VOCALOID'),
            ('{id}', '歌曲ID', '12345678'),
            ('{popularity}', '热度评分', '95'),
        ]
        
        print(f"{'变量':<20} {'说明':<25} {'示例'}")
        print("-" * 70)
        for var, desc, example in variables:
            print(f"{var:<20} {desc:<25} {example}")
        print()


def load_config_file(config_path: str) -> Dict:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  配置文件不存在: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式错误: {e}")
        return {}


def merge_config_with_args(config: Dict, args) -> Dict:
    """合并配置文件和命令行参数（命令行参数优先）"""
    merged = {
        'mkv_file': args.mkv_file or config.get('mkv_file'),
        'output': args.output or config.get('output'),
        'template': args.template if args.template != 'default' else config.get('template', 'default'),
        'custom_template': config.get('custom_template'),
        'recognition': {
            'strategy': args.strategy if args.strategy != 'start' else config.get('recognition', {}).get('strategy', 'start'),
            'offset': args.offset if args.offset != 5.0 else config.get('recognition', {}).get('offset', 5.0),
            'percentage': args.percentage if args.percentage != 0.5 else config.get('recognition', {}).get('percentage', 0.5),
            'duration': args.duration if args.duration != 3 else config.get('recognition', {}).get('duration', 3)
        },
        'tools': {
            'ffmpeg': args.ffmpeg or config.get('tools', {}).get('ffmpeg'),
            'mkvextract': args.mkvextract or config.get('tools', {}).get('mkvextract'),
            'mkvpropedit': args.mkvpropedit or config.get('tools', {}).get('mkvpropedit')
        },
        'options': {
            'no_backup': args.no_backup or config.get('options', {}).get('no_backup', False),
            'skip_check': args.skip_check or config.get('options', {}).get('skip_check', False)
        }
    }
    return merged


def create_default_config(config_path: str):
    """创建默认配置文件（包含所有可配置选项）"""
    default_config = {
        "mkv_file": None,
        "output": None,
        "template": "default",
        "custom_template": None,
        "recognition": {
            "strategy": "start",
            "offset": 5.0,
            "percentage": 0.5,
            "duration": 3
        },
        "tools": {
            "ffmpeg": None,
            "mkvextract": None,
            "mkvpropedit": None
        },
        "options": {
            "no_backup": False,
            "skip_check": False
        },
        "_comments": {
            "mkv_file": "MKV视频文件路径（也可通过命令行指定）",
            "output": "输出文件路径，null表示覆盖原文件",
            "template": "预设模板: default, with_trans, full, simple, artist_first, with_id, detailed, japanese, minimal",
            "custom_template": "自定义模板字符串，如 '{name} by {artists}'，设置后template参数无效",
            "recognition.strategy": "采样策略: start(开始), middle(中间), end(结尾), custom(自定义百分比)",
            "recognition.offset": "START策略的延迟秒数",
            "recognition.percentage": "CUSTOM策略的位置百分比(0.0-1.0)",
            "recognition.duration": "采样时长（秒），建议3-5秒",
            "tools": "工具路径，null表示自动检测",
            "options.no_backup": "是否禁用自动备份",
            "options.skip_check": "是否跳过工具检查"
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已创建默认配置文件: {config_path}")
    print(f"💡 提示: 配置文件中的选项会被命令行参数覆盖")


class AFPInstance:
    """音频指纹识别器"""
    DURATION: int = 3  # 采样时长（秒）
    SAMPLERATE: int = 8000  # 采样率（Hz）
    SAMPLECOUNT = DURATION * SAMPLERATE

    def __init__(self, afp_js_path: str = None):
        self.event_loop = asyncio.new_event_loop()
        
        if afp_js_path:
            self.afp_js_path = afp_js_path
        else:
            if getattr(sys, 'frozen', False):
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(__file__)
                
            self.afp_js_path = os.path.join(base_path, 'ncm-afp', 'docs', 'afp.js')
        
        if not os.path.exists(self.afp_js_path):
            raise FileNotFoundError(f"AFP JavaScript文件不存在: {self.afp_js_path}")
            
        # Pre-load the module to avoid recursion issues in repeated calls
        try:
            from pythonmonkey import require
            self.afp_module = require(self.afp_js_path)
        except Exception as e:
            print(f"Warning: Failed to pre-load AFP module: {e}")
            self.afp_module = None

    def generate_fingerprint(self, sample: list) -> str:
        """生成音频指纹"""
        assert len(sample) == self.SAMPLECOUNT, \
            f'期望 {self.SAMPLECOUNT} 个样本，实际收到 {len(sample)}'
        
        async def run():
            if self.afp_module:
                afp = self.afp_module
            else:
                from pythonmonkey import require
                afp = require(self.afp_js_path)
            return await afp.GenerateFP(sample)
        
        return self.event_loop.run_until_complete(run())


class MKVChapter:
    """MKV章节信息"""
    def __init__(self, uid: str, start_time: str, end_time: str = None, title: str = ""):
        self.uid = uid
        self.start_time = start_time  # 格式: HH:MM:SS.sss
        self.end_time = end_time
        self.title = title
        
    def __repr__(self):
        return f"<Chapter: {self.title} @ {self.start_time}>"
    
    @staticmethod
    def parse_time_to_seconds(time_str: str) -> float:
        """将时间字符串转换为秒数"""
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    @staticmethod
    def format_seconds_to_time(seconds: float) -> str:
        """将秒数转换为时间字符串"""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        millisecs = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"


class MKVChapterManager:
    """MKV章节管理器"""
    
    def __init__(self, mkv_file: str, mkvextract_path: str = "mkvextract", 
                 mkvpropedit_path: str = "mkvpropedit"):
        self.mkv_file = Path(mkv_file)
        self.mkvextract_path = mkvextract_path
        self.mkvpropedit_path = mkvpropedit_path
        
        if not self.mkv_file.exists():
            raise FileNotFoundError(f"MKV文件不存在: {mkv_file}")
        
        # 验证工具可用性
        self._verify_tools()
        
        # 验证工具可用性
        self._verify_tools()
    
    def _verify_tools(self):
        """验证MKVToolNix工具可用性"""
        for tool_name, tool_path in [("mkvextract", self.mkvextract_path), 
                                      ("mkvpropedit", self.mkvpropedit_path)]:
            is_valid, msg = verify_tool(tool_path, tool_name)
            if not is_valid:
                raise FileNotFoundError(
                    f"无法使用 {tool_name}: {msg}\n"
                    f"路径: {tool_path}\n"
                    f"请检查工具是否已安装，或使用 --{tool_name} 参数指定正确路径"
                )
    
    def extract_chapters(self) -> List[MKVChapter]:
        """从MKV文件中提取章节信息"""
        print(f"📖 正在提取章节信息: {self.mkv_file.name}")
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.xml', delete=False, encoding='utf-8') as tmp:
            tmp_path = tmp.name
        
        try:
            # 使用mkvextract提取章节
            cmd = [self.mkvextract_path, str(self.mkv_file), 'chapters', tmp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode != 0:
                raise RuntimeError(f"提取章节失败: {result.stderr}")
            
            # 解析XML章节文件
            with open(tmp_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            chapters = self._parse_chapter_xml(xml_content)
            print(f"✅ 找到 {len(chapters)} 个章节")
            return chapters
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _parse_chapter_xml(self, xml_content: str) -> List[MKVChapter]:
        """解析章节XML内容"""
        chapters = []
        
        # 使用正则表达式提取章节信息
        chapter_pattern = re.compile(
            r'<ChapterAtom>.*?<ChapterUID>(.*?)</ChapterUID>.*?'
            r'<ChapterTimeStart>(.*?)</ChapterTimeStart>.*?'
            r'(?:<ChapterTimeEnd>(.*?)</ChapterTimeEnd>.*?)?'
            r'<ChapterDisplay>.*?<ChapterString>(.*?)</ChapterString>',
            re.DOTALL
        )
        
        for match in chapter_pattern.finditer(xml_content):
            uid = match.group(1)
            start_time = match.group(2)
            end_time = match.group(3) if match.group(3) else None
            title = match.group(4)
            
            # Clean up time string (remove excessive precision, keep 3 decimal places)
            if '.' in start_time:
                parts = start_time.split('.')
                if len(parts[1]) > 3:
                    start_time = f"{parts[0]}.{parts[1][:3]}"
            
            if end_time and '.' in end_time:
                parts = end_time.split('.')
                if len(parts[1]) > 3:
                    end_time = f"{parts[0]}.{parts[1][:3]}"
            
            chapters.append(MKVChapter(uid, start_time, end_time, title))
        
        return chapters
    
    def update_chapters(self, chapters: List[MKVChapter], output_file: str = None):
        """更新MKV文件的章节信息"""
        output_file = output_file or str(self.mkv_file)
        
        print(f"💾 正在更新章节信息...")
        
        # 生成章节XML
        xml_content = self._generate_chapter_xml(chapters)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp:
            tmp.write(xml_content)
            tmp_path = tmp.name
        
        try:
            # 使用mkvpropedit更新章节
            cmd = [self.mkvpropedit_path, output_file, '--chapters', tmp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode != 0:
                raise RuntimeError(f"更新章节失败: {result.stderr}")
            
            print(f"✅ 章节信息已更新到: {Path(output_file).name}")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _generate_chapter_xml(self, chapters: List[MKVChapter]) -> str:
        """生成章节XML内容"""
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE Chapters SYSTEM "matroskachapters.dtd">',
            '<Chapters>',
            '  <EditionEntry>'
        ]
        
        for chapter in chapters:
            xml_parts.extend([
                '    <ChapterAtom>',
                f'      <ChapterUID>{chapter.uid}</ChapterUID>',
                f'      <ChapterTimeStart>{chapter.start_time}</ChapterTimeStart>',
            ])
            
            if chapter.end_time:
                xml_parts.append(f'      <ChapterTimeEnd>{chapter.end_time}</ChapterTimeEnd>')
            
            xml_parts.extend([
                '      <ChapterDisplay>',
                f'        <ChapterString>{chapter.title}</ChapterString>',
                '        <ChapterLanguage>und</ChapterLanguage>',
                '      </ChapterDisplay>',
                '    </ChapterAtom>'
            ])
        
        xml_parts.extend([
            '  </EditionEntry>',
            '</Chapters>'
        ])
        
        return '\n'.join(xml_parts)


class AudioRecognizer:
    """音频识别器"""
    
    def __init__(self, afp_instance: AFPInstance, ffmpeg_path: str = "ffmpeg"):
        self.afp = afp_instance
        self.ffmpeg_path = ffmpeg_path
    
    def extract_audio_sample(self, video_file: str, start_time: float, 
                            duration: int = 3) -> Optional[list]:
        """从视频中提取音频样本"""
        print(f"  🎵 提取音频片段: {start_time:.2f}s ~ {start_time + duration:.2f}s")
        
        cmd = [
            self.ffmpeg_path,
            '-ss', str(start_time),
            '-i', video_file,
            '-vn', # 禁用视频流，加快处理速度并减少定位问题
            '-t', str(duration),
            '-acodec', 'pcm_f32le',
            '-f', 'f32le',
            '-ar', str(self.afp.SAMPLERATE),
            '-ac', '1',
            '-'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=True
            )
            
            # 解析音频数据
            buffer = result.stdout
            expected_size = self.afp.SAMPLECOUNT * 4
            
            if len(buffer) < expected_size:
                print(f"  ⚠️  音频数据不足: {len(buffer)} < {expected_size} 字节")
                return None
            
            samples = list(unpack('<%df' % self.afp.SAMPLECOUNT, buffer[:expected_size]))
            return samples
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ FFmpeg错误: {e.stderr.decode('utf-8', errors='ignore')}")
            return None
    
    def recognize_song(self, samples: list) -> Optional[Dict]:
        """识别歌曲"""
        try:
            print(f"  🔍 生成音频指纹并识别...")
            fp = self.afp.generate_fingerprint(samples)
            result = GetMatchTrackByFP(fp, self.afp.DURATION)
            
            if result['code'] == 200 and result['data']['result']:
                song_info = result['data']['result'][0]['song']
                return {
                    'name': song_info['name'],
                    'artists': ', '.join([a['name'] for a in song_info['artists']]),
                    'album': song_info['album']['name'],
                    'id': song_info['id'],
                    'transName': song_info.get('transName', ''),
                    'popularity': song_info.get('popularity', 0)
                }
            else:
                print(f"  ❌ 未识别到歌曲")
                return None
                
        except Exception as e:
            print(f"  ❌ 识别失败: {e}")
            return None


class MKVAutoRename:
    """MKV自动重命名主程序"""
    
    def __init__(self, mkv_file: str, 
                 recognition_config: RecognitionConfig = None,
                 template: ChapterTemplate = None,
                 ffmpeg_path: str = "ffmpeg",
                 mkvextract_path: str = "mkvextract",
                 mkvpropedit_path: str = "mkvpropedit"):
        """
        Args:
            mkv_file: MKV文件路径
            recognition_config: 识别配置
            template: 章节标题模板
            ffmpeg_path: FFmpeg可执行文件路径
            mkvextract_path: mkvextract可执行文件路径
            mkvpropedit_path: mkvpropedit可执行文件路径
        """
        self.mkv_file = mkv_file
        self.recognition_config = recognition_config or RecognitionConfig()
        self.template = template or ChapterTemplate('default')
        
        self.chapter_manager = MKVChapterManager(mkv_file, mkvextract_path, mkvpropedit_path)
        self.afp = AFPInstance()
        self.recognizer = AudioRecognizer(self.afp, ffmpeg_path)
    
    def process(self, output_file: str = None, backup: bool = True):
        """执行自动识别和重命名"""
        print(f"\n{'='*60}")
        print(f"🎬 MKV章节自动识别与重命名")
        print(f"{'='*60}\n")
        print(f"📁 文件: {self.mkv_file}")
        
        # 1. 提取现有章节
        chapters = self.chapter_manager.extract_chapters()
        
        if not chapters:
            print("❌ 未找到章节信息")
            return
        
        # 2. 备份原始章节
        if backup:
            self._backup_chapters(chapters)
        
        # 3. 识别每个章节的歌曲
        print(f"\n{'='*60}")
        print(f"🎵 开始识别章节歌曲")
        print(f"{'='*60}\n")
        
        updated_count = 0
        for i, chapter in enumerate(chapters, 1):
            print(f"\n[{i}/{len(chapters)}] 处理章节: {chapter.title}")
            print(f"  ⏱️  时间: {chapter.start_time}")
            
            # 计算采样起始时间
            start_seconds = MKVChapter.parse_time_to_seconds(chapter.start_time)
            end_seconds = MKVChapter.parse_time_to_seconds(chapter.end_time) if chapter.end_time else None
            
            sample_start = self.recognition_config.calculate_sample_time(
                start_seconds, end_seconds
            )
            
            print(f"  📍 采样策略: {self.recognition_config.strategy.value}")
            print(f"  🎯 采样位置: {sample_start:.2f}s")
            
            # 提取音频样本
            samples = self.recognizer.extract_audio_sample(self.mkv_file, sample_start)
            
            if samples is None:
                print(f"  ⚠️  跳过此章节")
                continue
            
            # 识别歌曲
            song_info = self.recognizer.recognize_song(samples)
            
            if song_info:
                # 使用模板更新章节名称
                new_title = self.template.format(song_info)
                print(f"  ✅ 识别成功: {new_title}")
                chapter.title = new_title
                updated_count += 1
            else:
                print(f"  ⚠️  保持原标题: {chapter.title}")
        
        # 4. 更新章节信息
        if updated_count > 0:
            print(f"\n{'='*60}")
            print(f"💾 更新MKV章节信息")
            print(f"{'='*60}\n")
            self.chapter_manager.update_chapters(chapters, output_file)
            print(f"\n✅ 成功更新 {updated_count}/{len(chapters)} 个章节")
        else:
            print(f"\n⚠️  没有章节被更新")
    
    def _backup_chapters(self, chapters: List[MKVChapter]):
        """备份原始章节信息"""
        backup_file = Path(self.mkv_file).with_suffix('.chapters.backup.json')
        
        chapters_data = [
            {
                'uid': ch.uid,
                'start_time': ch.start_time,
                'end_time': ch.end_time,
                'title': ch.title
            }
            for ch in chapters
        ]
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(chapters_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 已备份原始章节到: {backup_file.name}")
    
    @staticmethod
    def restore_from_backup(mkv_file: str, backup_file: Optional[str] = None, 
                          mkvpropedit_path: str = "mkvpropedit"):
        """
        从备份文件还原章节信息
        
        Args:
            mkv_file: MKV文件路径
            backup_file: 备份文件路径（如果为None，自动查找）
            mkvpropedit_path: mkvpropedit可执行文件路径
        """
        print(f"\n{'='*60}")
        print(f"🔄 从备份还原章节信息")
        print(f"{'='*60}\n")
        
        mkv_path = Path(mkv_file)
        
        # 自动查找备份文件
        if backup_file is None:
            backup_path = mkv_path.with_suffix('.chapters.backup.json')
        else:
            backup_path = Path(backup_file)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_path}")
        
        print(f"📁 MKV文件: {mkv_path.name}")
        print(f"📄 备份文件: {backup_path.name}\n")
        
        # 读取备份文件
        print("📖 正在读取备份文件...")
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                chapters_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"备份文件格式错误: {e}")
        
        if not chapters_data:
            raise ValueError("备份文件中没有章节信息")
        
        # 转换为MKVChapter对象
        chapters = []
        for data in chapters_data:
            chapter = MKVChapter(
                uid=data['uid'],
                start_time=data['start_time'],
                end_time=data.get('end_time'),
                title=data['title']
            )
            chapters.append(chapter)
        
        print(f"✅ 找到 {len(chapters)} 个章节\n")
        
        # 显示章节预览
        print("章节列表预览：")
        for i, ch in enumerate(chapters[:5], 1):
            print(f"  [{i}] {ch.start_time} - {ch.title}")
        if len(chapters) > 5:
            print(f"  ... 还有 {len(chapters) - 5} 个章节")
        print()
        
        # 使用MKVChapterManager的静态方法更新章节（避免初始化检查mkvextract）
        print("💾 正在还原章节信息...")
        
        # 创建临时章节文件
        temp_chapters_file = mkv_path.with_suffix('.chapters.restore.txt')
        try:
            with open(temp_chapters_file, 'w', encoding='utf-8') as f:
                for i, chapter in enumerate(chapters):
                    # 使用章节索引作为ID，确保格式正确
                    chapter_id = f"{i:02d}"
                    f.write(f"CHAPTER{chapter_id}={chapter.start_time}\n")
                    f.write(f"CHAPTER{chapter_id}NAME={chapter.title}\n")
            
            # 使用mkvpropedit更新章节
            cmd = [mkvpropedit_path, str(mkv_path), '--chapters', str(temp_chapters_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"mkvpropedit执行失败: {result.stderr}")
            
        finally:
            # 删除临时文件
            if temp_chapters_file.exists():
                temp_chapters_file.unlink()
        
        print(f"\n✅ 成功从备份还原 {len(chapters)} 个章节！")
        print(f"📁 文件: {mkv_path.name}\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MKV视频章节自动识别与重命名工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  基本使用:
    %(prog)s video.mkv
    %(prog)s video.mkv -o output.mkv
  
  自定义采样策略:
    %(prog)s video.mkv --strategy start --offset 10
    %(prog)s video.mkv --strategy middle
    %(prog)s video.mkv --strategy custom --percentage 0.3
  
  自定义章节模板:
    %(prog)s video.mkv --template simple
    %(prog)s video.mkv --template "{name} by {artists}"
  
  使用配置文件:
    %(prog)s video.mkv --config config.json
  
  查看模板和策略:
    %(prog)s --list-templates
    %(prog)s --show-variables
  
  备份与还原:
    %(prog)s video.mkv --restore
    %(prog)s video.mkv --restore --backup-file custom_backup.json
        """
    )
    
    # 文件参数
    parser.add_argument('mkv_file', nargs='?', help='MKV视频文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（默认覆盖原文件）')
    
    # 识别策略参数
    strategy_group = parser.add_argument_group('识别策略选项')
    strategy_group.add_argument('--strategy', 
                               choices=['start', 'middle', 'end', 'custom'],
                               default='start',
                               help='采样策略 (默认: start)')
    strategy_group.add_argument('--offset', type=float, default=5.0,
                               help='从章节开始后的偏移秒数（用于start策略，默认: 5秒）')
    strategy_group.add_argument('--percentage', type=float, default=0.5,
                               help='章节位置百分比，0.0-1.0（用于custom策略，默认: 0.5）')
    strategy_group.add_argument('--duration', type=int, default=3,
                               help='采样时长（秒，默认: 3秒）')
    
    # 模板参数
    template_group = parser.add_argument_group('章节模板选项')
    template_group.add_argument('--template', default='default',
                               help='章节标题模板（预设名称或自定义格式字符串）')
    template_group.add_argument('--list-templates', action='store_true',
                               help='列出所有预设模板并退出')
    template_group.add_argument('--show-variables', action='store_true',
                               help='显示可用的模板变量并退出')
    
    # 配置文件
    config_group = parser.add_argument_group('配置文件选项')
    config_group.add_argument('--config', help='配置文件路径（JSON格式）')
    config_group.add_argument('--create-config', help='创建默认配置文件并退出')
    
    # 工具路径
    tool_group = parser.add_argument_group('工具路径选项')
    tool_group.add_argument('--ffmpeg', default=None,
                           help='FFmpeg可执行文件路径（留空自动检测）')
    tool_group.add_argument('--mkvextract', default=None,
                           help='mkvextract可执行文件路径（留空自动检测）')
    tool_group.add_argument('--mkvpropedit', default=None,
                           help='mkvpropedit可执行文件路径（留空自动检测）')
    
    # 其他选项
    other_group = parser.add_argument_group('其他选项')
    other_group.add_argument('--no-backup', action='store_true',
                            help='不备份原始章节信息')
    other_group.add_argument('--skip-check', action='store_true',
                            help='跳过依赖工具检查')
    other_group.add_argument('--restore', action='store_true',
                            help='从备份文件还原章节信息')
    other_group.add_argument('--backup-file',
                            help='指定备份文件路径（还原模式使用，默认为自动查找 .chapters.backup.json）')
    
    args = parser.parse_args()
    
    # 处理辅助命令
    if args.list_templates:
        ChapterTemplate.list_templates()
        return
    
    if args.show_variables:
        ChapterTemplate.show_available_variables()
        return
    
    if args.create_config:
        create_default_config(args.create_config)
        return
    
    # 从备份还原章节信息
    if args.restore:
        if not args.mkv_file:
            print("❌ 错误: 还原模式需要指定MKV文件路径")
            print("示例: python auto_rename_mkv_chapters.py video.mkv --restore")
            return
        
        # 获取mkvpropedit路径
        if args.skip_check:
            mkvpropedit_path = args.mkvpropedit or "mkvpropedit"
        else:
            if args.mkvpropedit:
                mkvpropedit_path = args.mkvpropedit
            else:
                mkvpropedit_path = find_tool_path('mkvpropedit')
                if not mkvpropedit_path:
                    print("❌ 错误: 找不到 mkvpropedit")
                    print("请安装 MKVToolNix 或使用 --mkvpropedit 指定路径")
                    return
        
        try:
            MKVAutoRename.restore_from_backup(
                mkv_file=args.mkv_file,
                backup_file=args.backup_file,
                mkvpropedit_path=mkvpropedit_path
            )
        except Exception as e:
            print(f"\n❌ 还原失败: {e}")
            import traceback
            traceback.print_exc()
        return
    
    # 加载并合并配置
    config = {}
    if args.config:
        config = load_config_file(args.config)
        print(f"📄 已加载配置文件: {args.config}\n")
    
    # 合并配置和命令行参数（命令行优先）
    merged_config = merge_config_with_args(config, args)
    
    # 验证必需参数
    if not merged_config['mkv_file']:
        parser.error("需要指定MKV文件路径（通过命令行或配置文件）")
        return
    
    # 创建识别配置
    recognition_config = RecognitionConfig(
        strategy=SamplingStrategy(merged_config['recognition']['strategy']),
        offset=merged_config['recognition']['offset'],
        percentage=merged_config['recognition']['percentage'],
        duration=merged_config['recognition']['duration']
    )
    
    # 创建章节模板
    if merged_config['custom_template']:
        template = ChapterTemplate('default')
        template.set_custom_template(merged_config['custom_template'])
        print(f"📝 使用自定义模板: {merged_config['custom_template']}")
    else:
        template = ChapterTemplate(merged_config['template'])
    
    print(f"\n⚙️  配置信息:")
    print(f"  采样策略: {recognition_config.strategy.value}")
    if recognition_config.strategy == SamplingStrategy.START:
        print(f"  偏移时间: {recognition_config.offset}秒")
    elif recognition_config.strategy == SamplingStrategy.CUSTOM:
        print(f"  位置百分比: {recognition_config.percentage * 100:.0f}%")
    print(f"  采样时长: {recognition_config.duration}秒")
    print(f"  章节模板: {template.template}\n")
    
    # 自动检测工具路径
    if not merged_config['options']['skip_check']:
        detected_tools = check_dependencies()
        if detected_tools is None:
            sys.exit(1)
        
        # 使用检测到的路径（如果配置和命令行都没有指定）
        ffmpeg_path = merged_config['tools']['ffmpeg'] or detected_tools.get('ffmpeg', 'ffmpeg')
        mkvextract_path = merged_config['tools']['mkvextract'] or detected_tools.get('mkvextract', 'mkvextract')
        mkvpropedit_path = merged_config['tools']['mkvpropedit'] or detected_tools.get('mkvpropedit', 'mkvpropedit')
    else:
        # 使用配置/命令行指定的值或默认值
        ffmpeg_path = merged_config['tools']['ffmpeg'] or 'ffmpeg'
        mkvextract_path = merged_config['tools']['mkvextract'] or 'mkvextract'
        mkvpropedit_path = merged_config['tools']['mkvpropedit'] or 'mkvpropedit'
    
    try:
        renamer = MKVAutoRename(
            merged_config['mkv_file'],
            recognition_config=recognition_config,
            template=template,
            ffmpeg_path=ffmpeg_path,
            mkvextract_path=mkvextract_path,
            mkvpropedit_path=mkvpropedit_path
        )
        
        renamer.process(
            output_file=merged_config['output'],
            backup=not merged_config['options']['no_backup']
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
