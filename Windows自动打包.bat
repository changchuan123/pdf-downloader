@echo off
chcp 65001 >nul
echo ====================================
echo     PDF下载器 Windows自动打包脚本
echo ====================================
echo.

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo 请先安装Python并确保添加到PATH
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

echo.
echo [2/4] 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败，尝试备用方法...
    python -m pip install -r requirements.txt
)

echo.
echo [3/4] 安装PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ❌ PyInstaller安装失败
    pause
    exit /b 1
)

echo.
echo [4/4] 开始打包...
echo 这可能需要几分钟时间，请耐心等待...
pyinstaller pdf_downloader_win.spec --clean

if errorlevel 1 (
    echo ❌ 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo ✅ 打包完成！
echo 可执行文件位置: dist\PDF下载器.exe
echo 文件大小: 
dir dist\PDF下载器.exe | findstr PDF下载器.exe

echo.
echo [测试] 是否要运行测试? (Y/N)
set /p test_choice=请选择: 
if /i "%test_choice%"=="Y" (
    echo 正在启动测试...
    cd dist
    "PDF下载器.exe"
    cd ..
)

echo.
echo 🎉 操作完成！
echo 您现在可以将 dist\PDF下载器.exe 复制到任何Windows电脑使用
pause 