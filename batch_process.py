#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理MKV文件的章节识别和重命名
支持目录递归扫描和并发处理
"""

import os
import sys
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import logging

# 导入主程序
from auto_rename_mkv_chapters import MKVAutoRename


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('batch_process.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, 
                 sample_offset: float = 5.0,
                 max_workers: int = 1,
                 recursive: bool = False,
                 skip_existing: bool = True,
                 ffmpeg_path: str = "ffmpeg",
                 mkvextract_path: str = "mkvextract",
                 mkvpropedit_path: str = "mkvpropedit"):
        """
        Args:
            sample_offset: 从章节开始后多少秒开始采样
            max_workers: 最大并发处理数（建议为1，避免API限流）
            recursive: 是否递归扫描子目录
            skip_existing: 是否跳过已有备份文件的视频
            ffmpeg_path: FFmpeg路径
            mkvextract_path: mkvextract路径
            mkvpropedit_path: mkvpropedit路径
        """
        self.sample_offset = sample_offset
        self.max_workers = max_workers
        self.recursive = recursive
        self.skip_existing = skip_existing
        self.ffmpeg_path = ffmpeg_path
        self.mkvextract_path = mkvextract_path
        self.mkvpropedit_path = mkvpropedit_path
        
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def find_mkv_files(self, directory: str) -> List[Path]:
        """查找MKV文件"""
        directory = Path(directory)
        
        if self.recursive:
            mkv_files = list(directory.rglob('*.mkv'))
        else:
            mkv_files = list(directory.glob('*.mkv'))
        
        logger.info(f"找到 {len(mkv_files)} 个MKV文件")
        return mkv_files
    
    def should_process(self, mkv_file: Path) -> bool:
        """判断是否应该处理该文件"""
        if self.skip_existing:
            backup_file = mkv_file.with_suffix('.chapters.backup.json')
            if backup_file.exists():
                logger.info(f"⏭️  跳过（已处理）: {mkv_file.name}")
                return False
        
        return True
    
    def process_single_file(self, mkv_file: Path) -> bool:
        """处理单个文件"""
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"开始处理: {mkv_file}")
            logger.info(f"{'='*80}")
            
            renamer = MKVAutoRename(
                str(mkv_file),
                sample_offset=self.sample_offset,
                ffmpeg_path=self.ffmpeg_path,
                mkvextract_path=self.mkvextract_path,
                mkvpropedit_path=self.mkvpropedit_path
            )
            
            renamer.process(backup=True)
            logger.info(f"✅ 完成: {mkv_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 失败: {mkv_file.name} - {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def process_directory(self, directory: str):
        """处理目录"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 批量处理模式")
        logger.info(f"{'='*80}")
        logger.info(f"目录: {directory}")
        logger.info(f"递归: {self.recursive}")
        logger.info(f"并发数: {self.max_workers}")
        logger.info(f"跳过已处理: {self.skip_existing}")
        logger.info(f"{'='*80}\n")
        
        # 查找所有MKV文件
        mkv_files = self.find_mkv_files(directory)
        
        if not mkv_files:
            logger.warning("未找到任何MKV文件")
            return
        
        # 过滤需要处理的文件
        files_to_process = [f for f in mkv_files if self.should_process(f)]
        
        self.stats['total'] = len(mkv_files)
        self.stats['skipped'] = len(mkv_files) - len(files_to_process)
        
        logger.info(f"\n需要处理: {len(files_to_process)} 个文件\n")
        
        if not files_to_process:
            logger.info("所有文件都已处理过")
            return
        
        # 串行或并行处理
        if self.max_workers == 1:
            # 串行处理（推荐，避免API限流）
            for i, mkv_file in enumerate(files_to_process, 1):
                logger.info(f"\n[{i}/{len(files_to_process)}] ")
                
                if self.process_single_file(mkv_file):
                    self.stats['success'] += 1
                else:
                    self.stats['failed'] += 1
        else:
            # 并行处理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.process_single_file, mkv_file): mkv_file
                    for mkv_file in files_to_process
                }
                
                for future in as_completed(futures):
                    if future.result():
                        self.stats['success'] += 1
                    else:
                        self.stats['failed'] += 1
        
        # 输出统计信息
        self._print_summary()
    
    def _print_summary(self):
        """打印处理摘要"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 处理完成")
        logger.info(f"{'='*80}")
        logger.info(f"总文件数: {self.stats['total']}")
        logger.info(f"成功: {self.stats['success']}")
        logger.info(f"失败: {self.stats['failed']}")
        logger.info(f"跳过: {self.stats['skipped']}")
        logger.info(f"{'='*80}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='批量处理MKV文件的章节识别和重命名',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s /path/to/videos
  %(prog)s /path/to/videos -r --offset 10
  %(prog)s /path/to/videos --workers 2 --no-skip
        """
    )
    
    parser.add_argument('directory', help='包含MKV文件的目录')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='递归扫描子目录')
    parser.add_argument('--offset', type=float, default=5.0,
                       help='从章节开始后多少秒开始采样（默认: 5秒）')
    parser.add_argument('--workers', type=int, default=1,
                       help='并发处理数（默认: 1，建议不要增加以避免API限流）')
    parser.add_argument('--no-skip', action='store_true',
                       help='不跳过已有备份文件的视频（重新处理所有文件）')
    parser.add_argument('--ffmpeg', default='ffmpeg',
                       help='FFmpeg可执行文件路径')
    parser.add_argument('--mkvextract', default='mkvextract',
                       help='mkvextract可执行文件路径')
    parser.add_argument('--mkvpropedit', default='mkvpropedit',
                       help='mkvpropedit可执行文件路径')
    
    args = parser.parse_args()
    
    try:
        processor = BatchProcessor(
            sample_offset=args.offset,
            max_workers=args.workers,
            recursive=args.recursive,
            skip_existing=not args.no_skip,
            ffmpeg_path=args.ffmpeg,
            mkvextract_path=args.mkvextract,
            mkvpropedit_path=args.mkvpropedit
        )
        
        processor.process_directory(args.directory)
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ 错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
