# ======================================
# MKV 章节自动识别工具 - 备份还原功能演示
# ======================================

Write-Host "
========================================" -ForegroundColor Cyan
Write-Host "功能演示：备份与还原" -ForegroundColor Cyan
Write-Host "========================================
" -ForegroundColor Cyan

# 1. 查看原始章节
Write-Host "1️⃣ 查看原始章节（前3个）：" -ForegroundColor Yellow
& 'C:\Program Files\MKVToolNix\mkvextract.exe' chapters 'c:\Users\gekdanhs\Desktop\Pack\source.mkv' | Select-String -Pattern 'ChapterString' | Select-Object -First 3

# 2. 修改章节（使用simple模板）
Write-Host "
2️⃣ 修改章节为简洁格式：" -ForegroundColor Yellow
Write-Host "命令: python auto_rename_mkv_chapters.py source.mkv --template simple" -ForegroundColor Gray
Write-Host "(演示模式，实际不执行)" -ForegroundColor DarkGray

# 3. 查看备份文件
Write-Host "
3️⃣ 备份文件已创建：" -ForegroundColor Yellow
Get-ChildItem 'c:\Users\gekdanhs\Desktop\Pack' -Filter '*.backup.json' | Format-Table Name, Length, LastWriteTime -AutoSize

# 4. 还原功能
Write-Host "
4️⃣ 从备份还原：" -ForegroundColor Yellow
Write-Host "命令: python auto_rename_mkv_chapters.py source.mkv --restore" -ForegroundColor Gray

# 5. 功能特点
Write-Host "
✨ 新增功能特点：" -ForegroundColor Green
Write-Host "  ✅ 自动备份原始章节" -ForegroundColor White
Write-Host "  ✅ 一键还原修改" -ForegroundColor White
Write-Host "  ✅ 支持自定义备份文件" -ForegroundColor White
Write-Host "  ✅ 可选择性禁用备份" -ForegroundColor White

# 6. 命令示例
Write-Host "
📝 常用命令：" -ForegroundColor Green
Write-Host "  # 从默认备份还原" -ForegroundColor Gray
Write-Host "  python auto_rename_mkv_chapters.py video.mkv --restore" -ForegroundColor White
Write-Host ""
Write-Host "  # 指定备份文件还原" -ForegroundColor Gray
Write-Host "  python auto_rename_mkv_chapters.py video.mkv --restore --backup-file custom.json" -ForegroundColor White
Write-Host ""
Write-Host "  # 修改时不创建备份" -ForegroundColor Gray
Write-Host "  python auto_rename_mkv_chapters.py video.mkv --no-backup" -ForegroundColor White

Write-Host "
========================================" -ForegroundColor Cyan
Write-Host "演示完成！所有功能已就绪 🎉" -ForegroundColor Cyan
Write-Host "========================================
" -ForegroundColor Cyan
