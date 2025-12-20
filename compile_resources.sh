#!/bin/bash

echo "正在编译资源文件..."
echo ""

echo "[1/2] 编译 Console 端资源文件..."
cd Console/Resources
python3 -m PyQt5.pyrcc_main Resources.qrc -o Resources.py
if [ $? -eq 0 ]; then
    echo "Console 端资源文件编译成功！"
else
    echo "Console 端资源文件编译失败！"
fi
cd ../..

echo ""
echo "[2/2] 编译 Client 端资源文件..."
cd Client/Resources
python3 -m PyQt5.pyrcc_main Resources.qrc -o Resources.py
if [ $? -eq 0 ]; then
    echo "Client 端资源文件编译成功！"
else
    echo "Client 端资源文件编译失败！"
fi
cd ../..

echo ""
echo "资源文件编译完成！"

