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
        """从URL中提取文件名，保持原始扩展名"""
        parsed_url = urlparse(url)
        filename = os.path.basename(unquote(parsed_url.path))
        
        # 如果URL中没有文件名，生成一个基于URL的文件名
        if not filename or filename == '/' or '.' not in filename:
            # 使用域名加上路径的hash作为文件名
            domain = parsed_url.netloc.replace('www.', '').replace('.', '_')
            url_hash = abs(hash(url)) % 10000
            filename = f"{domain}_{url_hash}.bin"  # 未知类型默认.bin
        
        return filename
    
    def get_file_extension_from_content_type(self, content_type):
        """根据Content-Type获取正确的文件扩展名（仅在URL无扩展名时使用）"""
        content_type = content_type.lower()
        
        if 'application/pdf' in content_type:
            return '.pdf'
        elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
            return '.jpg'
        elif 'image/png' in content_type:
            return '.png'
        elif 'image/gif' in content_type:
            return '.gif'
        elif 'image/webp' in content_type:
            return '.webp'
        elif 'text/plain' in content_type:
            return '.txt'
        elif 'text/html' in content_type:
            return '.html'
        elif 'application/json' in content_type:
            return '.json'
        elif 'application/zip' in content_type:
            return '.zip'
        else:
            return '.bin'  # 未知类型使用.bin
    
    def get_final_filename(self, custom_name, url):
        """获取最终文件名：优先使用URL扩展名，无扩展名时保持原样"""
        if custom_name:
            # 使用自定义文件名，结合URL的扩展名
            return self.combine_filename_with_url_extension(custom_name, url)
        else:
            # 直接从URL提取文件名
            return self.get_filename_from_url(url)
    
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
    
    def download_pdf(self, url, max_retries=3):
        """下载单个文件，保持原始扩展名"""
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=30, stream=True)
                response.raise_for_status()
                
                # 从URL获取文件名（保持原始扩展名）
                filename = self.get_final_filename(None, url)
                
                # 生成唯一文件名
                unique_filename = self.get_unique_filename(filename)
                file_path = self.download_folder / unique_filename
                
                # 保存文件
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print(f"成功下载: {unique_filename}")
                return True
                
            except requests.exceptions.Timeout:
                print(f"下载超时 (尝试 {attempt + 1}/{max_retries}): {url}")
                if attempt == max_retries - 1:
                    print(f"下载失败 - 超时: {url}")
                    return False
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                print(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {url} - {str(e)}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(2)
                
            except Exception as e:
                print(f"未知错误: {url} - {str(e)}")
                return False
        
        return False
    
    def download_from_excel(self, excel_file):
        """从Excel文件批量下载文件，使用指定的文件名 + URL扩展名"""
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file, header=None)
            
            if len(df.columns) < 2:
                print("错误：Excel文件至少需要两列（第一列：文件名，第二列：URL）")
                return
            
            # 第一列是文件名，第二列是URL
            filenames = df.iloc[:, 0].tolist()
            urls = df.iloc[:, 1].tolist()
            
            print(f"从Excel读取到 {len(urls)} 个下载任务")
            print("文件命名规则：使用Excel指定文件名 + URL中的扩展名")
            
            success_count = 0
            
            for i, (filename, url) in enumerate(zip(filenames, urls), 1):
                if pd.isna(url) or not str(url).strip():
                    print(f"跳过第 {i} 行：URL为空")
                    continue
                
                if pd.isna(filename) or not str(filename).strip():
                    print(f"跳过第 {i} 行：文件名为空")
                    continue
                
                url = str(url).strip()
                filename = str(filename).strip()
                
                print(f"\n[{i}/{len(urls)}] 下载: {filename}")
                print(f"URL: {url}")
                
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    response = requests.get(url, headers=headers, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    # 组合文件名：Excel指定名称 + URL扩展名
                    final_filename = self.get_final_filename(filename, url)
                    
                    # 生成唯一文件名
                    unique_filename = self.get_unique_filename(final_filename)
                    file_path = self.download_folder / unique_filename
                    
                    # 保存文件
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    print(f"成功: {unique_filename}")
                    success_count += 1
                    
                except Exception as e:
                    print(f"失败: {str(e)}")
                    continue
            
            print(f"\n下载完成！成功: {success_count}, 失败: {len(urls) - success_count}")
            
        except Exception as e:
            print(f"读取Excel文件时出错: {str(e)}")
            print("请确保Excel文件格式正确：第一列文件名，第二列URL")
    
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
                executor.submit(self.download_pdf, url): url
                for url in url_list
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success = future.result()
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
    
    def download_from_list_with_names(self, url_list, filename_list):
        """使用指定文件名批量下载文件，保持URL原始扩展名"""
        if not url_list:
            print("URL列表为空")
            return
        
        print(f"开始下载 {len(url_list)} 个文件（最大 {self.max_workers} 个并发）...")
        print("文件命名规则：使用指定文件名 + URL中的扩展名")
        
        # 重置计数器
        self.success_count = 0
        self.failed_count = 0
        
        # 逐个下载（简化逻辑）
        for url, filename in zip(url_list, filename_list):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=30, stream=True)
                response.raise_for_status()
                
                # 组合文件名：指定名称 + URL扩展名
                final_filename = self.get_final_filename(filename, url)
                
                # 生成唯一文件名
                unique_filename = self.get_unique_filename(final_filename)
                file_path = self.download_folder / unique_filename
                
                # 保存文件
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print(f"成功: {unique_filename}")
                self.success_count += 1
                
            except Exception as e:
                print(f"失败: {filename} - {str(e)}")
                self.failed_count += 1
        
        self.print_summary()

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

    def combine_filename_with_url_extension(self, custom_name, url):
        """将自定义文件名与URL的扩展名组合"""
        # 从URL获取原始文件名和扩展名
        parsed_url = urlparse(url)
        url_filename = os.path.basename(unquote(parsed_url.path))
        
        # 获取URL中的扩展名
        if url_filename and '.' in url_filename:
            url_extension = os.path.splitext(url_filename)[1]
        else:
            url_extension = ''
        
        # 移除自定义文件名中可能存在的扩展名
        custom_base = os.path.splitext(custom_name)[0]
        
        # 组合：自定义文件名 + URL的扩展名
        if url_extension:
            return f"{custom_base}{url_extension}"
        else:
            # 如果URL没有扩展名，保持自定义文件名原样
            return custom_name

def main():
    print("=== 文件批量下载器 ===")
    
    # 创建下载器实例
    downloader = PDFDownloader()
    
    while True:
        print("\n选择操作:")
        print("1. 从Excel文件批量下载")
        print("2. 从URL文件批量下载")
        print("3. 手动输入URL下载")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == '1':
            excel_file = input("请输入Excel文件路径（或直接回车使用当前目录下的test_urls.xlsx）: ").strip()
            if not excel_file:
                excel_file = "test_urls.xlsx"
                
            if not os.path.exists(excel_file):
                print(f"文件不存在: {excel_file}")
                continue
                
            downloader.download_from_excel(excel_file)
            
        elif choice == '2':
            url_file = input("请输入URL文件路径: ").strip()
            if not url_file or not os.path.exists(url_file):
                print("文件不存在")
                continue
                
            downloader.download_from_file(url_file)
            
        elif choice == '3':
            url = input("请输入要下载的URL: ").strip()
            if url:
                downloader.download_pdf(url)
            else:
                print("URL不能为空")
                
        elif choice == '4':
            print("退出程序")
            break
            
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
