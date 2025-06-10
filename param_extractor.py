import sys
import os
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 导入配置和工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SQLI_PARAMS, MAX_WORKERS
from utils.logger import get_logger
from utils.http_client import http_get, async_get
from utils.url_tools import is_valid_url, extract_links_from_html, has_sqli_param
from utils.file_utils import read_urls_from_file, write_urls_to_file, append_url_to_file

logger = get_logger("param_extractor")

class ParamExtractor:
    """URL参数提取器"""
    
    def __init__(self, input_file, output_file="output/extracted_urls.txt"):
        self.input_file = input_file
        self.output_file = output_file
        self.seen_urls = set()
        self.seen_domains = set()
        self.extracted_count = 0
    
    def extract_links(self, html, base_url):
        """从HTML中提取链接
        
        Args:
            html: HTML内容
            base_url: 基础URL
            
        Returns:
            提取的链接列表
        """
        links = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 提取所有链接
            for tag in soup.find_all("a", href=True):
                href = tag["href"]
                full_url = urljoin(base_url, href)
                if is_valid_url(full_url):
                    links.append(full_url)
            
            # 提取表单
            for form in soup.find_all("form", action=True):
                action = form.get("action")
                full_url = urljoin(base_url, action)
                if is_valid_url(full_url):
                    links.append(full_url)
        except Exception as e:
            logger.error(f"提取链接异常: {base_url}, {str(e)}")
        
        return links
    
    def filter_links(self, links):
        """过滤链接，只保留含SQL注入参数的链接
        
        Args:
            links: 链接列表
            
        Returns:
            过滤后的链接列表
        """
        filtered = []
        for url in links:
            if has_sqli_param(url) and url not in self.seen_urls:
                self.seen_urls.add(url)
                filtered.append(url)
                
                # 保存URL
                append_url_to_file(url, self.output_file)
                self.extracted_count += 1
                
                logger.info(f"提取到新URL: {url}")
        
        return filtered
    
    def process_url(self, url):
        """处理单个URL，提取参数
        
        Args:
            url: URL
            
        Returns:
            提取的链接列表
        """
        try:
            logger.info(f"处理URL: {url}")
            
            # 获取页面内容
            response = http_get(url)
            if not response or response.status_code != 200:
                logger.warning(f"获取页面失败: {url}")
                return []
            
            # 提取链接
            links = self.extract_links(response.text, url)
            logger.debug(f"从 {url} 提取了 {len(links)} 个链接")
            
            # 过滤链接
            filtered = self.filter_links(links)
            logger.info(f"从 {url} 提取了 {len(filtered)} 个有效链接")
            
            return filtered
        except Exception as e:
            logger.error(f"处理URL异常: {url}, {str(e)}")
            return []
    
    async def process_url_async(self, url):
        """异步处理单个URL
        
        Args:
            url: URL
            
        Returns:
            提取的链接列表
        """
        try:
            logger.info(f"异步处理URL: {url}")
            
            # 获取页面内容
            html = await async_get(url)
            if not html:
                logger.warning(f"异步获取页面失败: {url}")
                return []
            
            # 提取链接
            links = extract_links_from_html(html, url)
            logger.debug(f"从 {url} 异步提取了 {len(links)} 个链接")
            
            # 过滤链接
            filtered = self.filter_links(links)
            logger.info(f"从 {url} 异步提取了 {len(filtered)} 个有效链接")
            
            return filtered
        except Exception as e:
            logger.error(f"异步处理URL异常: {url}, {str(e)}")
            return []
    
    async def extract_params_async(self, max_workers=MAX_WORKERS):
        """异步提取参数
        
        Args:
            max_workers: 最大并发数
            
        Returns:
            提取的链接列表
        """
        # 读取URL列表
        urls = read_urls_from_file(self.input_file)
        if not urls:
            logger.error(f"无法读取URL列表: {self.input_file}")
            return []
        
        logger.info(f"开始处理 {len(urls)} 个URL，最大并发数: {max_workers}")
        
        # 创建信号量限制并发
        semaphore = asyncio.Semaphore(max_workers)
        
        async def process_with_semaphore(url):
            async with semaphore:
                return await self.process_url_async(url)
        
        # 创建任务
        tasks = [process_with_semaphore(url) for url in urls]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        
        # 合并结果
        extracted_urls = []
        for result in results:
            extracted_urls.extend(result)
        
        logger.info(f"参数提取完成，共提取 {self.extracted_count} 个URL")
        return list(self.seen_urls)
    
    def extract_params(self):
        """提取参数（同步版本）
        
        Returns:
            提取的链接列表
        """
        # 读取URL列表
        urls = read_urls_from_file(self.input_file)
        if not urls:
            logger.error(f"无法读取URL列表: {self.input_file}")
            return []
        
        logger.info(f"开始处理 {len(urls)} 个URL")
        
        # 处理每个URL
        for url in urls:
            self.process_url(url)
        
        logger.info(f"参数提取完成，共提取 {self.extracted_count} 个URL")
        return list(self.seen_urls)

async def main():
    """主函数"""
    # 创建参数提取器
    extractor = ParamExtractor("output/fofa_urls.txt", "output/extracted_urls.txt")
    
    # 异步提取参数
    await extractor.extract_params_async()

if __name__ == "__main__":
    asyncio.run(main()) 