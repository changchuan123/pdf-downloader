import os
import requests
from urllib.parse import urlparse, unquote
import time
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import sys
from datetime import datetime

class PDFDownloader:
    def __init__(self, download_folder="downloads", max_workers=5):
        """
        初始化PDF下载器
        
        Args:
            download_folder (str): 下载文件保存的文件夹路径
            max_workers (int): 最大并发下载数
        """
        self.download_folder = Path(download_folder)
        self.max_workers = max_workers
        self.session = requests.Session()
        
        # 设置请求头，模拟浏览器访问
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 创建下载文件夹
        self.download_folder.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.success_count = 0
        self.failed_count = 0
        self.failed_urls = []
        
        # 文件名计数器，用于处理重复文件名
        self.filename_counter = {}
        
        # 文件类型映射表 - Content-Type 到扩展名
        self.content_type_map = {
            # PDF文件
            'application/pdf': '.pdf',
            'application/x-pdf': '.pdf',
            
            # 图片文件
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg', 
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
            'image/tiff': '.tiff',
            
            # 文档文件
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-powerpoint': '.ppt',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            
            # 文本文件
            'text/plain': '.txt',
            'text/html': '.html',
            'text/css': '.css',
            'text/javascript': '.js',
            'application/json': '.json',
            'text/xml': '.xml',
            'application/xml': '.xml',
            
            # 压缩文件
            'application/zip': '.zip',
            'application/x-rar-compressed': '.rar',
            'application/x-7z-compressed': '.7z',
            'application/x-tar': '.tar',
            'application/gzip': '.gz',
            
            # 音频文件
            'audio/mpeg': '.mp3',
            'audio/wav': '.wav',
            'audio/flac': '.flac',
            'audio/aac': '.aac',
            
            # 视频文件
            'video/mp4': '.mp4',
            'video/avi': '.avi',
            'video/quicktime': '.mov',
            'video/x-msvideo': '.avi',
            'video/webm': '.webm',
            
            # 其他常见格式
            'application/octet-stream': None,  # 需要进一步检测
        }
        
        # 文件头签名检测（用于Content-Type不可靠的情况）
        self.file_signatures = {
            b'\x25\x50\x44\x46': '.pdf',  # PDF
            b'\xFF\xD8\xFF': '.jpg',       # JPEG
            b'\x89\x50\x4E\x47': '.png',   # PNG
            b'\x47\x49\x46\x38': '.gif',   # GIF
            b'\x42\x4D': '.bmp',           # BMP
            b'\x50\x4B\x03\x04': '.zip',   # ZIP (也可能是docx, xlsx等)
            b'\x50\x4B\x05\x06': '.zip',   # ZIP (空档案)
            b'\x50\x4B\x07\x08': '.zip',   # ZIP
            b'\xD0\xCF\x11\xE0': '.doc',   # DOC/XLS/PPT (老格式)
            b'\x52\x61\x72\x21': '.rar',   # RAR
            b'\x7F\x45\x4C\x46': '.elf',   # ELF执行文件
            b'\x4D\x5A': '.exe',           # Windows可执行文件
        }
    
    def detect_file_type_from_content(self, content_sample):
        """
        从文件内容检测文件类型
        
        Args:
            content_sample (bytes): 文件前几个字节
            
        Returns:
            str: 文件扩展名，如果无法识别返回None
        """
        if not content_sample:
            return None
            
        # 检查文件头签名
        for signature, extension in self.file_signatures.items():
            if content_sample.startswith(signature):
                return extension
        
        return None
    
    def detect_file_type_from_response(self, response, url):
        """
        从HTTP响应检测文件类型
        
        Args:
            response: requests.Response对象
            url (str): 请求的URL
            
        Returns:
            str: 检测到的文件扩展名
        """
        detected_ext = None
        
        # 1. 首先尝试从Content-Type检测
        content_type = response.headers.get('content-type', '').lower().split(';')[0].strip()
        if content_type in self.content_type_map:
            detected_ext = self.content_type_map[content_type]
            if detected_ext:
                print(f"🔍 从Content-Type检测到文件类型: {content_type} -> {detected_ext}")
        
        # 2. 如果Content-Type检测失败或者是application/octet-stream，尝试文件头检测
        if not detected_ext or content_type == 'application/octet-stream':
            # 读取前64字节进行文件头检测
            content_sample = b''
            try:
                for chunk in response.iter_content(chunk_size=64):
                    content_sample = chunk
                    break
                
                if content_sample:
                    header_ext = self.detect_file_type_from_content(content_sample)
                    if header_ext:
                        detected_ext = header_ext
                        print(f"🔍 从文件头检测到文件类型: {header_ext}")
                        
            except:
                pass
        
        # 3. 如果还是检测不到，尝试从URL路径提取
        if not detected_ext:
            parsed_url = urlparse(url)
            url_path = unquote(parsed_url.path).lower()
            
            # 常见扩展名映射
            url_extensions = {
                '.pdf': '.pdf', '.doc': '.doc', '.docx': '.docx',
                '.xls': '.xls', '.xlsx': '.xlsx', '.ppt': '.ppt', '.pptx': '.pptx',
                '.jpg': '.jpg', '.jpeg': '.jpg', '.png': '.png', '.gif': '.gif',
                '.bmp': '.bmp', '.webp': '.webp', '.svg': '.svg',
                '.txt': '.txt', '.html': '.html', '.htm': '.html',
                '.zip': '.zip', '.rar': '.rar', '.7z': '.7z',
                '.mp3': '.mp3', '.wav': '.wav', '.mp4': '.mp4', '.avi': '.avi'
            }
            
            for ext in url_extensions:
                if url_path.endswith(ext):
                    detected_ext = url_extensions[ext]
                    print(f"🔍 从URL路径检测到文件类型: {ext}")
                    break
        
        # 4. 如果所有方法都失败，根据Content-Type大类给默认扩展名
        if not detected_ext:
            if 'image' in content_type:
                detected_ext = '.jpg'
                print(f"🔍 根据Content-Type大类指定为图片: {detected_ext}")
            elif 'text' in content_type:
                detected_ext = '.txt'
                print(f"🔍 根据Content-Type大类指定为文本: {detected_ext}")
            elif 'application' in content_type:
                detected_ext = '.pdf'  # 默认假设是PDF
                print(f"🔍 无法识别具体类型，默认设为PDF: {detected_ext}")
            else:
                detected_ext = '.bin'  # 二进制文件
                print(f"🔍 完全无法识别，设为二进制文件: {detected_ext}")
        
        return detected_ext or '.unknown'
    
    def get_filename_from_url(self, url):
        """从URL中提取文件名"""
        parsed_url = urlparse(url)
        filename = os.path.basename(unquote(parsed_url.path))
        
        # 如果URL中没有文件名，生成一个基于URL的文件名
        if not filename or filename == '/' or '.' not in filename:
            # 使用域名加上路径的hash作为文件名
            domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
            url_hash = abs(hash(url)) % 10000
            filename = f"{domain}_{url_hash}"
            # 注意：这里不添加扩展名，会在下载时动态检测
        
        return filename
    
    def get_unique_filename(self, base_filename):
        """获取唯一的文件名，处理重复情况"""
        file_path = self.download_folder / base_filename
        
        # 如果文件不存在，直接返回
        if not file_path.exists():
            return base_filename
        
        # 处理重复文件名，添加-1、-2、-3等后缀
        name_stem = file_path.stem
        name_suffix = file_path.suffix
        counter = 1
        
        while True:
            new_filename = f"{name_stem}-{counter}{name_suffix}"
            new_file_path = self.download_folder / new_filename
            if not new_file_path.exists():
                return new_filename
            counter += 1
    
    def download_single_pdf(self, url):
        """
        下载单个PDF文件，使用URL自动提取的文件名，并智能检测文件类型
        
        Args:
            url (str): 文件的下载链接
        
        Returns:
            tuple: (成功标志, 文件路径或错误信息)
        """
        try:
            print(f"正在下载: {url}")
            
            # 发送请求下载文件
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 智能检测文件类型
            detected_extension = self.detect_file_type_from_response(response, url)
            
            # 从URL提取基础文件名
            base_filename = self.get_filename_from_url(url)
            
            # 如果基础文件名已经有扩展名，检查是否与检测到的一致
            if '.' in base_filename:
                current_ext = '.' + base_filename.split('.')[-1].lower()
                if current_ext != detected_extension:
                    # 扩展名不匹配，用检测到的扩展名替换
                    base_filename = base_filename.rsplit('.', 1)[0] + detected_extension
                    print(f"🔄 文件扩展名已更正为: {detected_extension}")
            else:
                # 没有扩展名，添加检测到的扩展名
                base_filename = base_filename + detected_extension
                print(f"➕ 已添加文件扩展名: {detected_extension}")
            
            # 获取唯一文件名（处理重复）
            unique_filename = self.get_unique_filename(base_filename)
            file_path = self.download_folder / unique_filename
            
            print(f"保存为: {unique_filename}")
            
            # 重新发起请求（因为之前的流可能已经被消费了）
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = file_path.stat().st_size
            print(f"✅ 下载完成: {unique_filename} ({file_size:,} bytes)")
            
            return True, str(file_path)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"下载失败 {url}: 网络错误 - {str(e)}"
            print(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"下载失败 {url}: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def download_from_list(self, url_list):
        """
        从URL列表批量下载PDF，使用URL自动提取文件名
        
        Args:
            url_list (list): PDF下载链接列表
        """
        print(f"开始批量下载 {len(url_list)} 个文件...")
        print(f"保存目录: {self.download_folder.absolute()}")
        print(f"文件命名: 使用URL自动提取文件名")
        print(f"并发数: {self.max_workers}")
        print("-" * 50)
        
        # 使用线程池并发下载
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(self.download_single_pdf, url): url
                for url in url_list
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success, result = future.result()
                    if success:
                        self.success_count += 1
                    else:
                        self.failed_count += 1
                        self.failed_urls.append(url)
                except Exception as e:
                    self.failed_count += 1
                    self.failed_urls.append(url)
                    print(f"任务执行异常 {url}: {str(e)}")
        
        self.print_summary()
    
    def download_from_file(self, urls_file_path, encoding='utf-8'):
        """
        从文件中读取URL列表并下载
        
        Args:
            urls_file_path (str): 包含URL列表的文件路径
            encoding (str): 文件编码
        """
        try:
            with open(urls_file_path, 'r', encoding=encoding) as f:
                urls = [line.strip() for line in f if line.strip()]
            
            print(f"从文件 {urls_file_path} 读取到 {len(urls)} 个URL")
            self.download_from_list(urls)
            
        except Exception as e:
            print(f"读取URL文件失败: {str(e)}")
    
    def download_from_excel(self, excel_path):
        """
        从Excel文件读取文件名和URL列表并下载
        第一列：文件名，第二列：URL
        
        Args:
            excel_path (str): Excel文件路径
        """
        try:
            # 读取Excel文件，不将第一行作为表头，指定引擎
            df = pd.read_excel(excel_path, header=None, engine='openpyxl')
            
            # 检查数据是否有效
            if len(df) == 0:
                print("❌ 错误: Excel文件为空")
                return
            
            # 第一列为文件名，第二列为URL
            urls = []
            filenames = []
            
            # 处理每一行数据
            for index, row in df.iterrows():
                filename_cell = row[0] if 0 in row else None
                url_cell = row[1] if 1 in row else None
                
                # 检查URL是否有效
                if pd.isna(url_cell) or not str(url_cell).strip():
                    print(f"⚠️  跳过第{index+1}行：URL为空")
                    continue
                
                # 处理文件名
                if pd.isna(filename_cell) or not str(filename_cell).strip():
                    # 如果文件名为空，从URL自动提取
                    filename = self.get_filename_from_url(str(url_cell).strip())
                    print(f"📝 第{index+1}行文件名为空，自动提取为: {filename}")
                else:
                    filename = str(filename_cell).strip()
                    # 注释掉强制添加扩展名的逻辑，保持原有扩展名
                    # if not filename.lower().endswith(('.pdf', '.doc', '.docx', '.txt', '.jpg', '.png', '.gif')):
                    #     filename += '.pdf'
                
                urls.append(str(url_cell).strip())
                filenames.append(filename)
            
            print(f"从Excel文件 {excel_path} 读取到 {len(urls)} 个下载任务")
            print("📝 文件命名: 使用Excel第一列指定的文件名")
            print("📝 重复文件: 自动添加-1、-2、-3等后缀")
            
            # 开始下载
            self.download_from_list_with_names(urls, filenames)
            
        except Exception as e:
            print(f"读取Excel文件失败: {str(e)}")
            print("请确保Excel文件格式正确：第一列为文件名，第二列为URL")
    
    def download_from_list_with_names(self, url_list, filename_list):
        """
        从URL列表和文件名列表批量下载
        
        Args:
            url_list (list): PDF下载链接列表
            filename_list (list): 对应的文件名列表
        """
        print(f"开始批量下载 {len(url_list)} 个文件...")
        print(f"保存目录: {self.download_folder.absolute()}")
        print(f"文件命名: 使用指定的文件名")
        print(f"并发数: {self.max_workers}")
        print("-" * 50)
        
        # 使用线程池并发下载
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self.download_single_pdf_with_name, url, filename): (url, filename)
                for url, filename in zip(url_list, filename_list)
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_task):
                url, filename = future_to_task[future]
                try:
                    success, result = future.result()
                    if success:
                        self.success_count += 1
                    else:
                        self.failed_count += 1
                        self.failed_urls.append(url)
                except Exception as e:
                    self.failed_count += 1
                    self.failed_urls.append(url)
                    print(f"任务执行异常 {url}: {str(e)}")
        
        self.print_summary()
    
    def download_single_pdf_with_name(self, url, filename):
        """
        下载单个文件，使用指定的文件名，并智能检测文件类型
        
        Args:
            url (str): 文件下载链接
            filename (str): 指定的文件名
        
        Returns:
            tuple: (成功标志, 文件路径或错误信息)
        """
        try:
            print(f"正在下载: {url}")
            
            # 发送请求下载文件
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 智能检测文件类型
            detected_extension = self.detect_file_type_from_response(response, url)
            
            # 处理用户指定的文件名
            if '.' in filename:
                # 用户指定的文件名有扩展名，检查是否与检测到的一致
                current_ext = '.' + filename.split('.')[-1].lower()
                if current_ext != detected_extension:
                    # 扩展名不匹配，给用户提示并使用检测到的扩展名
                    base_name = filename.rsplit('.', 1)[0]
                    filename = base_name + detected_extension
                    print(f"🔄 文件扩展名已从 {current_ext} 更正为: {detected_extension}")
                else:
                    print(f"✅ 文件扩展名正确: {current_ext}")
            else:
                # 用户指定的文件名没有扩展名，添加检测到的扩展名
                filename = filename + detected_extension
                print(f"➕ 已添加文件扩展名: {detected_extension}")
            
            # 获取唯一文件名（处理重复）
            unique_filename = self.get_unique_filename(filename)
            file_path = self.download_folder / unique_filename
            
            print(f"保存为: {unique_filename}")
            
            # 重新发起请求（因为之前的流可能已经被消费了）
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = file_path.stat().st_size
            print(f"✅ 下载完成: {unique_filename} ({file_size:,} bytes)")
            
            return True, str(file_path)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"下载失败 {url}: 网络错误 - {str(e)}"
            print(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"下载失败 {url}: {str(e)}"
            print(error_msg)
            return False, error_msg

    def print_summary(self):
        """打印下载统计信息"""
        print("\n" + "=" * 50)
        print("下载完成统计:")
        print(f"成功: {self.success_count}")
        print(f"失败: {self.failed_count}")
        print(f"总计: {self.success_count + self.failed_count}")
        
        if self.failed_urls:
            print("\n失败的URL:")
            for url in self.failed_urls:
                print(f"  - {url}")


# 使用示例
if __name__ == "__main__":
    # 修复文件路径问题：获取exe所在目录或当前工作目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe文件
        project_path = os.path.dirname(sys.executable)
    else:
        # 如果是Python脚本
        project_path = os.path.dirname(os.path.abspath(__file__))
    
    # 如果上述路径在临时目录中，使用当前工作目录
    if "Temp" in project_path or "temp" in project_path or "_MEI" in project_path:
        project_path = os.getcwd()
    
    # 优先使用正式文件
    urls_file = os.path.join(project_path, "urls.xlsx")
    if not os.path.exists(urls_file):
        test_file = os.path.join(project_path, "test_urls.xlsx")
        if os.path.exists(test_file):
            urls_file = test_file
    
    # 创建按时间戳命名的下载文件夹
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    download_folder = os.path.join(project_path, f"下载_{current_time}")
    
    # 检查必要文件是否存在
    if not os.path.exists(urls_file):
        print(f"❌ 错误: 未找到Excel文件")
        print(f"请在程序目录创建以下文件之一:")
        print(f"  - test_urls.xlsx (测试文件)")
        print(f"  - urls.xlsx (正式文件)")
        print(f"当前目录: {project_path}")
        print("\nExcel文件格式要求:")
        print("  第一列: 文件名")
        print("  第二列: 下载链接URL")
        input("按回车键退出...")
        exit(1)
    
    print("PDF批量下载工具")
    print("=" * 50)
    print(f"程序目录: {project_path}")
    print(f"Excel文件: {urls_file}")
    print(f"下载目录: {download_folder}")
    print(f"下载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # 创建下载器实例
    downloader = PDFDownloader(
        download_folder=download_folder,
        max_workers=3  # 并发下载数
    )
    
    # 直接使用Excel文件下载
    if urls_file.lower().endswith(('.xlsx', '.xls')):
        downloader.download_from_excel(urls_file)
    else:
        downloader.download_from_file(urls_file)
    
    print("\n✅ 下载任务完成！")
    print(f"文件保存在: {download_folder}")
    input("按回车键退出...")
