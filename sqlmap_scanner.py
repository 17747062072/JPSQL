import sys
import os
import time
import asyncio

# 导入配置和工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAX_WORKERS
from utils.logger import get_logger
from utils.sqlmap_client import SQLMapClient, AsyncSQLMapClient
from utils.file_utils import read_urls_from_file, save_result_to_file, save_vulnerability
from utils.notifier import notifier

logger = get_logger("sqlmap_scanner")

class SQLMapScanner:
    """SQLMap扫描器"""
    
    def __init__(self, input_file="output/extracted_urls.txt"):
        self.input_file = input_file
        self.client = SQLMapClient()
        self.async_client = AsyncSQLMapClient()
        self.scanned_count = 0
        self.vulnerable_count = 0
        self.failed_count = 0
        self.vulnerable_urls = []
    
    def scan_url(self, url):
        """扫描单个URL
        
        Args:
            url: 要扫描的URL
            
        Returns:
            扫描结果
        """
        logger.info(f"开始扫描URL: {url}")
        
        try:
            # 使用SQLMap API扫描
            result = self.client.scan_url(url)
            self.scanned_count += 1
            
            # 检查是否发现漏洞
            if result and result.get("data"):
                self.vulnerable_count += 1
                self.vulnerable_urls.append(url)
                
                # 保存漏洞信息
                save_vulnerability(url, result)
                
                # 发送通知
                notifier.notify_vulnerability(url, result)
                
                logger.warning(f"发现SQL注入漏洞: {url}")
            else:
                logger.info(f"未发现SQL注入漏洞: {url}")
            
            # 保存扫描结果
            save_result_to_file(url, result)
            
            return result
        except Exception as e:
            self.failed_count += 1
            logger.error(f"扫描URL异常: {url}, {str(e)}")
            return None
    
    async def scan_url_async(self, url):
        """异步扫描单个URL
        
        Args:
            url: 要扫描的URL
            
        Returns:
            扫描结果
        """
        logger.info(f"异步扫描URL: {url}")
        
        try:
            # 使用SQLMap API异步扫描
            result = await self.async_client.scan_url(url)
            self.scanned_count += 1
            
            # 检查是否发现漏洞
            if result and result.get("data"):
                self.vulnerable_count += 1
                self.vulnerable_urls.append(url)
                
                # 保存漏洞信息
                save_vulnerability(url, result)
                
                # 发送通知
                notifier.notify_vulnerability(url, result)
                
                logger.warning(f"发现SQL注入漏洞: {url}")
            else:
                logger.info(f"未发现SQL注入漏洞: {url}")
            
            # 保存扫描结果
            save_result_to_file(url, result)
            
            return result
        except Exception as e:
            self.failed_count += 1
            logger.error(f"异步扫描URL异常: {url}, {str(e)}")
            return None
    
    def scan(self):
        """扫描所有URL（同步版本）
        
        Returns:
            扫描统计信息
        """
        # 读取URL列表
        urls = read_urls_from_file(self.input_file)
        if not urls:
            logger.error(f"无法读取URL列表: {self.input_file}")
            return {}
        
        total_urls = len(urls)
        logger.info(f"开始扫描 {total_urls} 个URL")
        
        # 扫描每个URL
        for url in urls:
            self.scan_url(url)
        
        # 统计信息
        stats = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": total_urls,
            "scanned": self.scanned_count,
            "vulnerable": self.vulnerable_count,
            "failed": self.failed_count,
            "vulnerable_urls": self.vulnerable_urls
        }
        
        # 发送扫描完成通知
        notifier.notify_scan_complete(stats)
        
        logger.info(f"扫描完成，共扫描 {self.scanned_count} 个URL，发现 {self.vulnerable_count} 个漏洞")
        return stats
    
    async def scan_async(self, max_workers=MAX_WORKERS):
        """异步扫描所有URL
        
        Args:
            max_workers: 最大并发数
            
        Returns:
            扫描统计信息
        """
        # 读取URL列表
        urls = read_urls_from_file(self.input_file)
        if not urls:
            logger.error(f"无法读取URL列表: {self.input_file}")
            return {}
        
        total_urls = len(urls)
        logger.info(f"开始异步扫描 {total_urls} 个URL，最大并发数: {max_workers}")
        
        # 创建信号量限制并发
        semaphore = asyncio.Semaphore(max_workers)
        
        async def scan_with_semaphore(url):
            async with semaphore:
                return await self.scan_url_async(url)
        
        # 创建任务
        tasks = [scan_with_semaphore(url) for url in urls]
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        
        # 统计信息
        stats = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": total_urls,
            "scanned": self.scanned_count,
            "vulnerable": self.vulnerable_count,
            "failed": self.failed_count,
            "vulnerable_urls": self.vulnerable_urls
        }
        
        # 发送扫描完成通知
        notifier.notify_scan_complete(stats)
        
        logger.info(f"异步扫描完成，共扫描 {self.scanned_count} 个URL，发现 {self.vulnerable_count} 个漏洞")
        return stats

async def main():
    """主函数"""
    # 创建扫描器
    scanner = SQLMapScanner()
    
    # 异步扫描
    await scanner.scan_async()

if __name__ == "__main__":
    asyncio.run(main()) 