@echo off
echo 正在编译资源文件...
echo.

echo [1/2] 编译 Console 端资源文件...
cd Console\Resources
python -m PyQt5.pyrcc_main Resources.qrc -o Resources.py
if %errorlevel% equ 0 (
    echo Console 端资源文件编译成功！
) else (
    echo Console 端资源文件编译失败！
)
cd ..\..

echo.
echo [2/2] 编译 Client 端资源文件...
cd Client\Resources
python -m PyQt5.pyrcc_main Resources.qrc -o Resources.py
if %errorlevel% equ 0 (
    echo Client 端资源文件编译成功！
) else (
    echo Client 端资源文件编译失败！
)
cd ..\..

echo.
echo 资源文件编译完成！
pause

