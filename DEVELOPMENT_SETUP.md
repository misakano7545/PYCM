# PYCM 开发环境配置指南

## 系统要求

- **操作系统**: Windows 10/11, Linux, macOS
- **Python 版本**: Python 3.7 或更高版本（推荐 Python 3.8+）
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 500MB 可用空间

## 步骤 1: 安装 Python

### Windows

1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载 Python 3.8 或更高版本
3. 运行安装程序，**务必勾选 "Add Python to PATH"**
4. 验证安装：
   ```bash
   python --version
   pip --version
   ```

### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip

# 验证安装
python3 --version
pip3 --version
```

### macOS

```bash
# 使用 Homebrew
brew install python3

# 或从官网下载安装包
# https://www.python.org/downloads/macos/

# 验证安装
python3 --version
pip3 --version
```

## 步骤 2: 克隆项目

```bash
# 使用 Git 克隆项目
git clone https://github.com/yang-zhongtian/PYCM.git
cd PYCM

# 或直接下载 ZIP 文件并解压
```

## 步骤 3: 创建虚拟环境（推荐）

### Windows

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 激活后，命令提示符前会显示 (venv)
```

### Linux/macOS

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 激活后，命令提示符前会显示 (venv)
```

## 步骤 4: 安装依赖

```bash
# 确保虚拟环境已激活（命令提示符前有 (venv)）

# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

**注意**: 项目依赖包括：
- PyQt5~=5.15.6

## 步骤 5: 编译资源文件

项目使用 Qt 资源文件（.qrc），需要编译为 Python 模块。

### 安装 PyQt5 工具（如果还没有）

```bash
# Windows/Linux/macOS
pip install pyqt5-tools

# 或者如果已安装 PyQt5，工具通常已包含在内
```

### 编译资源文件

**推荐方法**：使用 Python 模块方式（适用于所有平台）

#### Console（教师端）资源文件

```bash
# Windows/Linux/macOS（从项目根目录运行）
python -m PyQt5.pyrcc_main Console\Resources\Resources.qrc -o Console\Resources\Resources.py

# Linux/macOS 路径分隔符
python -m PyQt5.pyrcc_main Console/Resources/Resources.qrc -o Console/Resources/Resources.py
```

#### Client（学生端）资源文件

```bash
# Windows（从项目根目录运行）
python -m PyQt5.pyrcc_main Client\Resources\Resources.qrc -o Client\Resources\Resources.py

# Linux/macOS 路径分隔符
python -m PyQt5.pyrcc_main Client/Resources/Resources.qrc -o Client/Resources/Resources.py
```

**替代方法 1**：使用提供的编译脚本（最简单）

```bash
# Windows（双击运行或在命令行执行）
compile_resources.bat

# Linux/macOS
chmod +x compile_resources.sh
./compile_resources.sh
```

**替代方法 2**：如果 `pyrcc5` 命令可用（已添加到 PATH）

```bash
# Console 端
cd Console\Resources
pyrcc5 Resources.qrc -o Resources.py
cd ..\..

# Client 端
cd Client\Resources
pyrcc5 Resources.qrc -o Resources.py
cd ..\..
```

**注意**: 
- ✅ **推荐使用** `python -m PyQt5.pyrcc_main` 方式，无需配置 PATH，适用于所有平台
- 如果修改了 `.qrc` 文件，需要重新编译资源文件
- 编译后的 `Resources.py` 文件会被 Git 忽略（已在 .gitignore 中）

## 步骤 6: 编译 UI 文件（可选）

如果修改了 `.ui` 文件，需要重新编译为 Python 文件：

```bash
# 编译单个 UI 文件
pyuic5 SettingsUI.ui -o SettingsUI.py

# 或使用 Python 模块方式
python -m PyQt5.uic.pyuic SettingsUI.ui -o SettingsUI.py
```

## 步骤 7: 运行项目

### 运行教师端（Console）

```bash
# Windows
python Console\ConsoleMain.py

# Linux/macOS
python3 Console/ConsoleMain.py
```

### 运行学生端（Client）

```bash
# Windows
python Client\ClientMain.py

# Linux/macOS
python3 Client/ClientMain.py
```

## 开发工具推荐

### IDE/编辑器

- **PyCharm** (推荐): 专业 Python IDE，对 PyQt5 支持良好
- **VS Code**: 轻量级编辑器，需要安装 Python 扩展
- **Qt Creator**: 用于编辑 `.ui` 文件

### 有用的 VS Code 扩展

- Python
- Pylance
- Python Docstring Generator

### 有用的 PyCharm 插件

- Qt Designer Integration
- Python

## 常见问题

### 1. 找不到 `pyrcc5` 或 `pyuic5` 命令

**解决方案**（推荐）:
```bash
# 使用 Python 模块方式（无需配置 PATH）
# 编译资源文件
python -m PyQt5.pyrcc_main Console\Resources\Resources.qrc -o Console\Resources\Resources.py
python -m PyQt5.pyrcc_main Client\Resources\Resources.qrc -o Client\Resources\Resources.py

# 编译 UI 文件
python -m PyQt5.uic.pyuic Console\UI\SettingsUI.ui -o Console\UI\SettingsUI.py
```

**其他方法**:
```bash
# 方法 1: 安装 pyqt5-tools（可能包含命令行工具）
pip install pyqt5-tools

# 方法 2: 添加到 PATH（Windows）
# 找到 PyQt5 安装目录（通常在 Python\Scripts 或 site-packages\PyQt5），添加到系统 PATH
```

### 2. 导入错误：`No module named 'Resources'`

**解决方案**: 确保已编译资源文件（步骤 5）

### 3. 界面显示异常或样式丢失

**解决方案**: 
- 确保资源文件已正确编译
- 检查 `Resources.py` 文件是否存在
- 重启应用程序

### 4. 网络功能无法使用

**解决方案**:
- 检查防火墙设置
- 确保在同一局域网内
- 检查网络适配器配置

### 5. 数据库文件问题

**解决方案**:
- Console 端会在首次运行时自动创建 `config.db`
- 如果数据库损坏，可以删除 `Console/config.db` 重新创建

## 开发工作流

1. **修改 UI 文件** (`.ui`):
   ```bash
   # 使用 Qt Designer 编辑 .ui 文件
   # 然后编译为 .py 文件
   pyuic5 SettingsUI.ui -o SettingsUI.py
   ```

2. **修改资源文件** (`.qrc`):
   ```bash
   # 编辑 Resources.qrc
   # 然后编译为 Resources.py（从项目根目录运行）
   python -m PyQt5.pyrcc_main Console\Resources\Resources.qrc -o Console\Resources\Resources.py
   python -m PyQt5.pyrcc_main Client\Resources\Resources.qrc -o Client\Resources\Resources.py
   ```

3. **修改 Python 代码**:
   - 直接编辑 `.py` 文件
   - 运行程序测试

4. **测试**:
   ```bash
   # 运行教师端
   python Console\ConsoleMain.py
   
   # 运行学生端（另一个终端）
   python Client\ClientMain.py
   ```

## 调试模式

项目支持调试模式，创建 `DEBUG` 文件即可启用详细日志：

```bash
# Windows
cd Console
type nul > DEBUG
cd ..

# Linux/macOS
cd Console
touch DEBUG
cd ..
```

## 下一步

- 查看项目 README 了解功能
- 查看代码注释了解实现细节
- 根据需要修改和扩展功能

## 获取帮助

- 查看项目 Issues: https://github.com/yang-zhongtian/PYCM/issues
- 查看项目 Wiki（如果有）

---

**祝开发愉快！** 🎉

