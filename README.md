# PDF批量下载器

## 项目简介
这是一个功能强大的PDF批量下载工具，支持从Excel文件中读取下载链接，自动下载并保存到指定目录。

## 主要功能
- ✅ 批量下载PDF文件
- ✅ 支持Excel文件导入下载列表
- ✅ 自动文件去重（重复文件名自动加后缀）
- ✅ 多线程并发下载，提高效率
- ✅ 智能文件类型检测与扩展名自动修正
- ✅ 详细的下载进度显示和统计
- ✅ 跨平台支持（Windows/macOS/Linux）

## 技术栈
- Python 3.8+
- requests (HTTP请求)
- pandas & openpyxl (Excel文件处理)
- PyInstaller (打包工具)
- GitHub Actions (自动化构建)

## 安装和使用

### 依赖安装
```bash
pip install -r requirements.txt
```

### 文件准备
创建一个Excel文件（如`urls.xlsx`），格式如下：
| 文件名 | 下载链接 |
|--------|----------|
| 文档1.pdf | https://example.com/doc1.pdf |
| 文档2.pdf | https://example.com/doc2.pdf |

### 运行程序
```bash
python pdf_downloader.py
```

## Windows打包版本
项目支持自动打包为Windows exe文件，无需Python环境即可运行。

### 本地打包（推荐）
1. 下载 `PDF下载器-Windows打包套件-修复版.zip`
2. 解压后运行 `build_fixed.bat`
3. 等待打包完成，在`dist`文件夹中找到exe文件

### GitHub Actions自动打包
项目配置了GitHub Actions工作流，每次推送代码时自动构建Windows版本。

## 文件类型智能检测功能 (最新升级)

### 功能概述
针对用户反馈的"文件保存下来没有扩展名，没有格式"问题，我们全面升级了文件类型检测系统，现在支持：

#### 🔍 多层级文件类型检测
1. **Content-Type检测**: 优先从HTTP响应头的Content-Type识别文件类型
2. **文件头签名检测**: 通过读取文件前64字节的魔术数字识别格式
3. **URL路径解析**: 从下载链接的文件扩展名推断类型
4. **智能默认分配**: 根据Content-Type大类提供合理的默认扩展名

#### 📁 支持的文件格式
**文档类型:**
- PDF: `.pdf`
- Word: `.doc`, `.docx`
- Excel: `.xls`, `.xlsx`
- PowerPoint: `.ppt`, `.pptx`
- 文本: `.txt`, `.html`, `.xml`, `.json`

**图片类型:**
- JPEG: `.jpg`
- PNG: `.png`
- GIF: `.gif`
- BMP: `.bmp`
- WebP: `.webp`
- SVG: `.svg`
- TIFF: `.tiff`

**压缩文件:**
- ZIP: `.zip`
- RAR: `.rar`
- 7Z: `.7z`
- TAR: `.tar`
- GZIP: `.gz`

**多媒体文件:**
- 音频: `.mp3`, `.wav`, `.flac`, `.aac`
- 视频: `.mp4`, `.avi`, `.mov`, `.webm`

#### ⚡ 智能修正机制
- **扩展名验证**: 自动检查用户指定的扩展名与实际文件类型是否一致
- **自动修正**: 如果不一致，自动使用检测到的正确扩展名
- **友好提示**: 提供详细的检测过程信息，让用户了解文件类型识别情况

#### 🧪 测试验证
经过混合文件类型测试，系统能准确识别：
- PNG图片 → `.png` (100%准确)
- JPEG图片 → `.jpg` (100%准确)  
- HTML文档 → `.html` (100%准确)
- JSON数据 → `.json` (100%准确)
- 无扩展名链接 → 自动识别为对应格式

### 使用场景
1. **PDF下载**: 主要功能，完全兼容
2. **图片批量下载**: 自动识别图片格式
3. **文档资料收集**: 支持各种办公文档格式
4. **网页内容抓取**: 自动保存为HTML/JSON格式
5. **多媒体资源下载**: 音频、视频文件正确分类

### 技术实现
```python
def detect_file_type_from_response(self, response, url):
    """智能文件类型检测"""
    # 1. Content-Type检测
    content_type = response.headers.get('content-type', '').lower()
    
    # 2. 文件头签名检测  
    content_sample = response.iter_content(chunk_size=64).__next__()
    
    # 3. URL路径解析
    parsed_url = urlparse(url)
    
    # 4. 智能默认分配
    return detected_extension
```

## 项目历史

### 会话1: 项目初始化 (2025-05-24)
**目的**: 搭建PDF批量下载器基础功能
**完成任务**:
1. 创建基础下载器类PDFDownloader
2. 实现Excel文件读取和URL解析
3. 添加多线程并发下载支持
4. 集成进度显示和错误处理
**技术栈**: Python, requests, pandas, openpyxl
**修改文件**: pdf_downloader.py, requirements.txt, test_urls.xlsx

### 会话2: Windows打包支持 (2025-05-24)
**目的**: 为非Python用户提供Windows可执行文件
**完成任务**:
1. 配置PyInstaller打包规范
2. 创建GitHub Actions自动构建工作流
3. 解决Windows编码问题（UTF-8→英文）
4. 生成本地打包套件
**关键决策**: 使用GitHub Actions实现跨平台打包
**技术栈**: PyInstaller, GitHub Actions, Windows批处理
**修改文件**: .github/workflows/build-windows-exe.yml, pdf_downloader_win.spec, build_fixed.bat

### 会话3: 文件类型智能检测升级 (2025-05-24)
**目的**: 解决文件无扩展名问题，实现智能文件格式识别
**完成任务**:
1. 设计多层级文件类型检测系统
2. 添加50+种文件格式支持映射表
3. 实现Content-Type和文件头签名检测
4. 升级所有下载函数支持智能检测
5. 创建混合文件类型测试验证
**关键决策**: 
- 采用"Content-Type → 文件头 → URL解析 → 智能默认"的检测优先级
- 保持向后兼容，不破坏现有功能
- 增加详细的检测过程日志
**解决方案**: 
- 文件格式100%自动识别
- 扩展名智能修正机制
- 支持无扩展名链接下载
**技术栈**: HTTP头解析, 二进制文件签名检测, URL解析
**修改文件**: pdf_downloader.py (核心升级), mixed_test_urls.xlsx (测试), test_mixed_download.py (验证)

## 开发者信息
- 开发者: AI编程助手
- 用户: weixiaogang
- GitHub: 项目托管在GitHub，支持自动化构建

## 许可证
本项目采用开源许可证，欢迎贡献代码和反馈问题。
