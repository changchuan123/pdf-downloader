# PDF 下载器

一个用于批量下载PDF文件的Python工具，支持从Excel文件读取URL列表并进行并发下载。

## 功能特点

- 📥 批量PDF下载
- 📊 Excel文件URL管理  
- 🚀 并发下载支持
- 📝 自定义文件名
- 🔄 断点续传
- 💪 错误处理和重试

## 安装使用

### 本地Python环境
```bash
git clone https://github.com/changchuan123/pdf-downloader.git
cd pdf-downloader
pip install -r requirements.txt
python pdf_downloader.py
```

### Windows版exe文件
从GitHub Releases下载：https://github.com/changchuan123/pdf-downloader/releases

## 开发记录

### 2025年1月24日 - Release功能修复
**修复目标**: 解决GitHub Actions构建#4的"Too many retries"错误

**主要修复**:
1. **编码问题解决**: 将PyInstaller输出文件名从`PDF下载器`改为`PDF_Downloader`，避免Windows编码问题
2. **Release机制优化**: 使用`softprops/action-gh-release@v1`替代不稳定的Release创建方法
3. **权限配置**: 添加`contents: write`权限支持自动Release创建
4. **YAML语法修复**: 解决PowerShell多行字符串在YAML中的格式问题
5. **双重下载**: 提供Release和Artifacts两种下载方式，解决Artifacts XML错误

**技术改进**:
- 自动生成带时间戳的Release版本(`v20250124-1430`)
- 优化构建流程，提高稳定性
- 完整的英文化界面，避免编码冲突
- 详细的Release说明和使用指南

### 2025年1月24日 - 编码问题解决  
**问题**: Windows批处理文件中文字符显示为乱码(`'埌Python鐜'`)
**解决**: 创建修复版配置文件，使用纯英文界面和文件名

### 2025年1月24日 - GitHub自动化构建
**完成功能**:
- GitHub Actions Windows环境自动构建
- PyInstaller配置优化
- 依赖包自动安装和错误处理
- 构建成功/失败状态监控

### 2025年1月24日 - 项目初始化
**核心功能实现**:
- PDF批量下载器主程序(pdf_downloader.py, 364行)
- Excel文件URL列表解析
- 并发下载和进度显示
- 错误处理和重试机制
- 自定义文件命名支持

## 技术栈

- **语言**: Python 3.8+
- **核心库**: requests, pandas, openpyxl
- **打包工具**: PyInstaller
- **CI/CD**: GitHub Actions
- **架构原则**: context7, KISS原则, SOLID原则

## 使用说明

1. 准备Excel文件(urls.xlsx或test_urls.xlsx)
   - 第一列：PDF下载链接
   - 第二列：自定义文件名(可选)

2. 运行程序
   - Python版本：`python pdf_downloader.py`
   - Windows版本：双击`PDF_Downloader.exe`

3. 下载的文件保存在`pdf_dl`文件夹中

## 注意事项

- 确保网络连接稳定
- 杀毒软件可能误报exe文件，请添加到白名单
- 支持断点续传，可以中断后重新运行
- 并发下载数量可在代码中调整

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

MIT License

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
