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
        
    def get_filename_from_url(self, url):
        """从URL中提取文件名"""
        parsed_url = urlparse(url)
        filename = os.path.basename(unquote(parsed_url.path))
        
        # 如果URL中没有文件名，生成一个基于URL的文件名
        if not filename or filename == '/' or '.' not in filename:
            # 使用域名加上路径的hash作为文件名
            domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
            url_hash = abs(hash(url)) % 10000
            filename = f"{domain}_{url_hash}.pdf"
        
        # 确保有扩展名
        if not filename.lower().endswith(('.pdf', '.doc', '.docx', '.txt', '.jpg', '.png', '.gif')):
            filename += '.pdf'
            
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
        下载单个PDF文件，使用URL自动提取的文件名
        
        Args:
            url (str): PDF文件的下载链接
        
        Returns:
            tuple: (成功标志, 文件路径或错误信息)
        """
        try:
            # 从URL提取文件名
            filename = self.get_filename_from_url(url)
            
            # 获取唯一文件名（处理重复）
            unique_filename = self.get_unique_filename(filename)
            file_path = self.download_folder / unique_filename
            
            print(f"正在下载: {url}")
            print(f"保存为: {unique_filename}")
            
            # 发送请求下载文件
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 检查Content-Type并确定文件扩展名
            content_type = response.headers.get('content-type', '').lower()
            
            # 根据Content-Type调整扩展名
            if 'application/pdf' in content_type or 'pdf' in content_type:
                if not unique_filename.lower().endswith('.pdf'):
                    unique_filename = f"{Path(unique_filename).stem}.pdf"
                    file_path = self.download_folder / unique_filename
            elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
                if not unique_filename.lower().endswith(('.jpg', '.jpeg')):
                    unique_filename = f"{Path(unique_filename).stem}.jpg"
                    file_path = self.download_folder / unique_filename
            elif 'image/png' in content_type:
                if not unique_filename.lower().endswith('.png'):
                    unique_filename = f"{Path(unique_filename).stem}.png"
                    file_path = self.download_folder / unique_filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = file_path.stat().st_size
            print(f"下载完成: {unique_filename} ({file_size} bytes)")
            
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
                    # 确保有扩展名
                    if not filename.lower().endswith(('.pdf', '.doc', '.docx', '.txt', '.jpg', '.png', '.gif')):
                        filename += '.pdf'
                
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
        下载单个文件，使用指定的文件名
        
        Args:
            url (str): 文件下载链接
            filename (str): 指定的文件名
        
        Returns:
            tuple: (成功标志, 文件路径或错误信息)
        """
        try:
            # 获取唯一文件名（处理重复）
            unique_filename = self.get_unique_filename(filename)
            file_path = self.download_folder / unique_filename
            
            print(f"正在下载: {url}")
            print(f"保存为: {unique_filename}")
            
            # 发送请求下载文件
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = file_path.stat().st_size
            print(f"下载完成: {unique_filename} ({file_size} bytes)")
            
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
    
    # 优先使用测试文件
    test_file = os.path.join(project_path, "test_urls.xlsx")
    if os.path.exists(test_file):
        urls_file = test_file
    else:
        urls_file = os.path.join(project_path, "urls.xlsx")
    
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
