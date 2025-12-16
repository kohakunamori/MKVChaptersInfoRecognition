# ======================================
# 配置文件功能演示
# ======================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "配置文件完整支持演示" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. 创建配置文件
Write-Host "1️⃣ 创建配置文件：" -ForegroundColor Yellow
Write-Host "命令: python auto_rename_mkv_chapters.py --create-config demo_config.json" -ForegroundColor Gray
python auto_rename_mkv_chapters.py --create-config demo_config.json

# 2. 查看配置文件内容
Write-Host "`n2️⃣ 配置文件内容（部分）：" -ForegroundColor Yellow
Get-Content demo_config.json | Select-Object -First 15

# 3. 修改配置文件
Write-Host "`n3️⃣ 修改配置文件：" -ForegroundColor Yellow
$config = Get-Content demo_config.json | ConvertFrom-Json
$config.template = "simple"
$config.recognition.strategy = "middle"
$config | ConvertTo-Json -Depth 10 | Set-Content demo_config.json
Write-Host "✅ 已修改: template=simple, strategy=middle" -ForegroundColor Green

# 4. 配置文件优先级
Write-Host "`n4️⃣ 配置优先级演示：" -ForegroundColor Yellow
Write-Host "配置文件设置: template=simple" -ForegroundColor Gray
Write-Host "命令行参数: --template full" -ForegroundColor Gray
Write-Host "实际使用: template=full (命令行优先)" -ForegroundColor Green

# 5. 使用场景
Write-Host "`n5️⃣ 实用场景：" -ForegroundColor Yellow
Write-Host ""
Write-Host "  场景A - 完全使用配置文件：" -ForegroundColor Cyan
Write-Host "    python auto_rename_mkv_chapters.py --config my_config.json" -ForegroundColor White
Write-Host ""
Write-Host "  场景B - 配置 + 命令行覆盖：" -ForegroundColor Cyan
Write-Host "    python auto_rename_mkv_chapters.py --config base.json video.mkv --template full" -ForegroundColor White
Write-Host ""
Write-Host "  场景C - 批量处理：" -ForegroundColor Cyan
Write-Host "    Get-ChildItem *.mkv | ForEach-Object {" -ForegroundColor White
Write-Host "        python auto_rename_mkv_chapters.py --config batch.json `$_.FullName" -ForegroundColor White
Write-Host "    }" -ForegroundColor White

# 6. 支持的配置项
Write-Host "`n6️⃣ 所有可配置项：" -ForegroundColor Yellow
Write-Host "  ✅ mkv_file - 输入文件路径" -ForegroundColor White
Write-Host "  ✅ output - 输出文件路径" -ForegroundColor White
Write-Host "  ✅ template - 章节模板" -ForegroundColor White
Write-Host "  ✅ custom_template - 自定义模板" -ForegroundColor White
Write-Host "  ✅ recognition - 识别策略配置" -ForegroundColor White
Write-Host "  ✅ tools - 工具路径配置" -ForegroundColor White
Write-Host "  ✅ options - 其他选项" -ForegroundColor White

# 7. 配置文件优势
Write-Host "`n7️⃣ 配置文件优势：" -ForegroundColor Yellow
Write-Host "  📄 集中管理所有配置" -ForegroundColor Green
Write-Host "  🔄 配置可重用" -ForegroundColor Green
Write-Host "  📝 支持版本控制" -ForegroundColor Green
Write-Host "  🎯 灵活组合使用" -ForegroundColor Green
Write-Host "  👥 便于团队协作" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "查看完整文档: CONFIG_GUIDE.md" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 清理
Remove-Item demo_config.json -ErrorAction SilentlyContinue
