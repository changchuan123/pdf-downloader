# PDF批量下载工具

## 功能
- 从Excel文件(urls.xlsx)批量下载PDF文件
- 支持自定义文件名(fp列)
- 多线程并发下载
- 自动重命名重复文件
- 兼容Windows/Linux/macOS

## 安装

### 1. 安装Python
确保系统已安装Python 3.7+:
```bash
python --version
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 准备Excel文件
创建urls.xlsx文件，包含两列：
- urls: PDF下载链接
- fp: 自定义文件名(可选)

## 使用方法
1. 将urls.xlsx放在程序目录
2. 运行程序:
```bash
python pdf_downloader.py
```

## Windows部署建议

### 方法1: 直接运行Python脚本
1. 安装Python和依赖
2. 双击pdf_downloader.py运行

### 方法2: 打包为EXE
使用PyInstaller打包:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed pdf_downloader.py
```
打包后的exe在dist目录

### 注意事项
1. 确保网络连接正常
2. Excel文件需使用.xlsx格式
3. 下载的文件保存在pdf_dl目录
4. 失败记录会显示在控制台

## 示例urls.xlsx
| urls | fp |
|------|----|
| http://example.com/1.pdf | 文件1.pdf |
| http://example.com/2.pdf | 文件2.pdf |

---

## 更新日志

### 2025-01-24 - EXE打包完成

#### 会话主要目的
将PDF下载器项目封装成可执行文件（exe），使其能在未安装Python的电脑上独立运行。

#### 完成的主要任务
1. **环境准备**：检查并安装必要的Python依赖包
   - requests>=2.25.1 - HTTP请求库
   - pandas>=1.3.0 - 数据处理库 
   - openpyxl>=3.0.0 - Excel文件处理
   - pyinstaller>=6.0.0 - Python打包工具

2. **应用测试**：验证程序在当前环境下能正常运行
   - 成功读取test_urls.xlsx测试文件
   - 验证下载功能正常工作
   - 确认并发下载和错误处理机制

3. **打包配置优化**：更新PyInstaller配置文件
   - 添加隐含导入：pandas, openpyxl, requests等关键库
   - 包含数据文件：test_urls.xlsx, urls.xlsx
   - 设置中文名称：PDF下载器
   - 优化打包参数

4. **可执行文件生成**：使用PyInstaller成功打包
   - 生成单一可执行文件：dist/PDF下载器
   - 文件大小：26MB
   - 目标架构：macOS ARM64

5. **功能验证**：测试打包后的可执行文件
   - 验证独立运行能力
   - 确认URL读取和下载功能正常
   - 测试文件保存和统计功能

#### 关键决策和解决方案
1. **网络问题处理**：遇到pip安装超时，采用逐个安装依赖的策略
2. **打包配置**：通过spec文件精确控制打包内容，确保所有依赖正确包含
3. **文件路径处理**：程序能自动适应打包后的临时目录环境
4. **中文命名**：可执行文件使用中文名称"PDF下载器"，便于用户识别

#### 使用的技术栈
- **Python 3.13.3**：主要开发语言
- **PyInstaller 6.13.0**：Python应用打包工具
- **pandas 2.2.3**：Excel文件处理和数据操作
- **requests 2.32.3**：HTTP下载功能
- **openpyxl 3.1.5**：Excel文件读写支持
- **threading/concurrent.futures**：并发下载实现

#### 修改的文件
1. **pdf_downloader.spec**：更新打包配置
   - 添加隐含导入列表
   - 包含数据文件
   - 设置可执行文件名称

2. **新增文件**：
   - **使用说明.txt**：详细的exe使用指南
   - **dist/PDF下载器**：最终生成的可执行文件

3. **README.md**：添加本次更新的详细记录

#### 最终成果
生成了一个26MB的独立可执行文件，可以在任何macOS ARM64设备上运行，无需安装Python环境。用户只需将可执行文件和URL配置文件放在同一目录下即可使用完整的PDF批量下载功能。
