import os
import requests
from urllib.parse import urlparse, unquote
import time
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

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
        
    def get_filename_from_url(self, url):
        """从URL中提取文件名"""
        parsed_url = urlparse(url)
        filename = os.path.basename(unquote(parsed_url.path))
        
        # 如果URL中没有文件名，生成一个
        if not filename:
            filename = f"file_{hash(url) % 100000}"
            
        return filename
    
    def download_single_pdf(self, url, custom_filename=None):
        """
        下载单个PDF文件
        
        Args:
            url (str): PDF文件的下载链接
            custom_filename (str): 自定义文件名（可选）
        
        Returns:
            tuple: (成功标志, 文件路径或错误信息)
        """
        try:
            # 确定文件名
            if custom_filename:
                filename = custom_filename
                if not filename.lower().endswith('.pdf'):
                    filename += '.pdf'
            else:
                filename = self.get_filename_from_url(url)
            
            file_path = self.download_folder / filename
            
            # 如果文件已存在，添加序号
            counter = 1
            original_path = file_path
            while file_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                file_path = self.download_folder / f"{stem}_{counter}{suffix}"
                counter += 1
            
            print(f"正在下载: {url}")
            print(f"保存为: {file_path}")
            
            # 发送请求下载文件
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 检查Content-Type并确定文件扩展名
            content_type = response.headers.get('content-type', '').lower()
            file_ext = os.path.splitext(filename)[1].lower()
            
            # 根据Content-Type确定扩展名
            if not file_ext:
                if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                    file_ext = '.jpg'
                elif 'image/png' in content_type:
                    file_ext = '.png'
                elif 'image/gif' in content_type:
                    file_ext = '.gif'
                elif 'application/pdf' in content_type or 'pdf' in content_type:
                    file_ext = '.pdf'
                elif 'text/html' in content_type:
                    file_ext = '.html'
                else:
                    file_ext = '.bin'  # 默认二进制文件
                
                # 更新文件名
                filename = f"{os.path.splitext(filename)[0]}{file_ext}"
                file_path = file_path.with_name(filename)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = file_path.stat().st_size
            print(f"下载完成: {file_path} ({file_size} bytes)")
            
            return True, str(file_path)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"下载失败 {url}: 网络错误 - {str(e)}"
            print(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"下载失败 {url}: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def download_from_list(self, url_list, filename_list=None):
        """
        从URL列表批量下载PDF
        
        Args:
            url_list (list): PDF下载链接列表
            filename_list (list): 对应的文件名列表（可选）
        """
        print(f"开始批量下载 {len(url_list)} 个PDF文件...")
        print(f"保存目录: {self.download_folder.absolute()}")
        print(f"并发数: {self.max_workers}")
        print("-" * 50)
        
        # 准备下载任务
        tasks = []
        for i, url in enumerate(url_list):
            custom_name = filename_list[i] if filename_list and i < len(filename_list) else None
            tasks.append((url, custom_name))
        
        # 使用线程池并发下载
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self.download_single_pdf, url, filename): (url, filename)
                for url, filename in tasks
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
    
    def download_from_files(self, urls_file_path, filenames_file_path=None, encoding='utf-8'):
        """
        从文件中读取URL列表和文件名列表并下载
        
        Args:
            urls_file_path (str): 包含URL列表的文件路径
            filenames_file_path (str): 包含文件名列表的文件路径（可选）
            encoding (str): 文件编码
        """
        # 检查是否是Excel文件
        if urls_file_path.lower().endswith(('.xlsx', '.xls')):
            return self.download_from_excel(urls_file_path)
        try:
            # 读取URL列表
            with open(urls_file_path, 'r', encoding=encoding) as f:
                urls = [line.strip() for line in f if line.strip()]
            
            print(f"从文件 {urls_file_path} 读取到 {len(urls)} 个URL")
            
            # 读取文件名列表（如果提供）
            filenames = None
            if filenames_file_path:
                try:
                    with open(filenames_file_path, 'r', encoding=encoding) as f:
                        filenames = [line.strip() for line in f if line.strip()]
                    
                    print(f"从文件 {filenames_file_path} 读取到 {len(filenames)} 个文件名")
                    
                    # 检查数量是否匹配
                    if len(urls) != len(filenames):
                        print(f"警告: URL数量({len(urls)})与文件名数量({len(filenames)})不匹配")
                        print("将使用较短列表的长度进行下载")
                        min_len = min(len(urls), len(filenames))
                        urls = urls[:min_len]
                        filenames = filenames[:min_len]
                        
                except Exception as e:
                    print(f"读取文件名文件失败: {str(e)}")
                    print("将使用默认文件名下载")
                    filenames = None
            
            # 开始下载
            self.download_from_list(urls, filenames)
            
        except Exception as e:
            print(f"读取文件失败: {str(e)}")
    
    def download_from_excel(self, excel_path):
        """
        从Excel文件读取URL和文件名列表并下载
        
        Args:
            excel_path (str): Excel文件路径
        """
        try:
            # 读取Excel文件，不将第一行作为表头
            df = pd.read_excel(excel_path, header=None)
            
            # 检查数据是否有效
            if len(df) == 0:
                print("❌ 错误: Excel文件为空")
                return
            
            # 第一列为urls，第二列为fp
            urls = []
            filenames = []
            
            # 处理每个单元格，可能包含多个URL
            for url_cell, name_cell in zip(df[0], df[1]):
                if pd.isna(url_cell):
                    continue
                    
                # 分割单元格中的多个URL（支持逗号/分号/空格分隔）
                cell_urls = []
                for sep in [',', ';', ' ']:
                    if sep in str(url_cell):
                        cell_urls = [u.strip() for u in str(url_cell).split(sep) if u.strip()]
                        break
                
                if not cell_urls:
                    cell_urls = [str(url_cell).strip()]
                
                # 处理对应的文件名
                if pd.isna(name_cell):
                    cell_filenames = [None] * len(cell_urls)
                else:
                    # 同样分割文件名
                    cell_filenames = []
                    for sep in [',', ';', ' ']:
                        if sep in str(name_cell):
                            cell_filenames = [n.strip() for n in str(name_cell).split(sep) if n.strip()]
                            break
                    
                    if not cell_filenames or len(cell_filenames) != len(cell_urls):
                        # 如果分割不匹配，使用第一个文件名加上序号
                        base_name = str(name_cell).strip()
                        cell_filenames = [f"{base_name}_{i+1}" for i in range(len(cell_urls))]
                
                urls.extend(cell_urls)
                filenames.extend(cell_filenames)
            
            print(f"从Excel文件 {excel_path} 读取到 {len(urls)} 个URL和 {len(filenames)} 个文件名")
            
            # 开始下载
            self.download_from_list(urls, filenames)
            
        except Exception as e:
            print(f"读取Excel文件失败: {str(e)}")

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
    # 定义文件路径
    project_path = os.path.dirname(os.path.abspath(__file__))
    # 优先使用测试文件
    test_file = os.path.join(project_path, "test_urls.xlsx")
    if os.path.exists(test_file):
        urls_file = test_file
    else:
        urls_file = os.path.join(project_path, "urls.xlsx")
    txt_urls_file = os.path.join(project_path, "urls.txt")
    filenames_file = os.path.join(project_path, "fp.txt")
    download_folder = os.path.join(project_path, "pdf_dl")
    
    # 检查必要文件是否存在
    if not os.path.exists(urls_file):
        print(f"⚠️  urls.xlsx 文件不存在于 {urls_file}")
        # 检查是否有txt文件作为备用
        if os.path.exists(txt_urls_file):
            print("✅ 检测到urls.txt文件，将使用txt文件进行下载")
            urls_file = txt_urls_file
        else:
            print(f"❌ 错误: 未找到urls.xlsx或urls.txt文件")
            print("请在该路径创建 urls.xlsx 文件，包含'urls'和'fp'列")
            exit(1)
    
    print("PDF批量下载工具")
    print("=" * 50)
    print(f"项目路径: {project_path}")
    print(f"URL文件: {urls_file}")
    print(f"文件名文件: {filenames_file}")
    print(f"下载目录: {download_folder}")
    print("-" * 50)
    
    # 创建下载器实例
    downloader = PDFDownloader(
        download_folder=download_folder,
        max_workers=3  # 并发下载数
    )
    
    # 检查文件名文件是否存在
    if os.path.exists(filenames_file):
        print("✅ 使用自定义文件名进行下载")
        downloader.download_from_files(urls_file, filenames_file)
    else:
        print("⚠️  fp.txt 不存在，将使用默认文件名")
        downloader.download_from_file(urls_file)
    
    print("\n✅ 下载任务完成！")
    print(f"文件保存在: {download_folder}")
