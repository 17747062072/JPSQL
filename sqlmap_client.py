import sys
import os
import json
import time
import asyncio

# 导入配置和工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SQLMAP_API_URL, SQLMAP_THREADS, SQLMAP_TIMEOUT, SQLMAP_LEVEL, SQLMAP_RISK
from utils.logger import get_logger, log_exception
from utils.http_client import http_get, http_post

logger = get_logger("sqlmap_client")

class SQLMapClient:
    """SQLMap API客户端"""
    
    def __init__(self, api_url=SQLMAP_API_URL):
        self.api_url = api_url
        self.headers = {'Content-Type': 'application/json'}
    
    def create_task(self):
        """创建新任务"""
        try:
            url = f"{self.api_url}/task/new"
            response = http_get(url)
            if response and response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    task_id = data.get("taskid")
                    logger.info(f"创建SQLMap任务成功: {task_id}")
                    return task_id
                else:
                    logger.error(f"创建SQLMap任务失败: {data.get('message', '未知错误')}")
            else:
                logger.error(f"创建SQLMap任务失败: 无效响应")
        except Exception as e:
            log_exception(logger, e, "创建SQLMap任务异常")
        
        return None
    
    def set_options(self, task_id, options):
        """设置任务选项"""
        try:
            url = f"{self.api_url}/option/{task_id}/set"
            response = http_post(url, json=options)
            if response and response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info(f"设置SQLMap选项成功: {task_id}")
                    return True
                else:
                    logger.error(f"设置SQLMap选项失败: {data.get('message', '未知错误')}")
            else:
                logger.error(f"设置SQLMap选项失败: 无效响应")
        except Exception as e:
            log_exception(logger, e, f"设置SQLMap选项异常: {task_id}")
        
        return False
    
    def start_scan(self, task_id, options=None):
        """开始扫描"""
        try:
            url = f"{self.api_url}/scan/{task_id}/start"
            data = options or {}
            response = http_post(url, json=data)
            if response and response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info(f"启动SQLMap扫描成功: {task_id}")
                    return True
                else:
                    logger.error(f"启动SQLMap扫描失败: {data.get('message', '未知错误')}")
            else:
                logger.error(f"启动SQLMap扫描失败: 无效响应")
        except Exception as e:
            log_exception(logger, e, f"启动SQLMap扫描异常: {task_id}")
        
        return False
    
    def get_status(self, task_id):
        """获取任务状态"""
        try:
            url = f"{self.api_url}/scan/{task_id}/status"
            response = http_get(url)
            if response and response.status_code == 200:
                data = response.json()
                status = data.get("status")
                logger.debug(f"SQLMap任务状态: {task_id} = {status}")
                return status
            else:
                logger.error(f"获取SQLMap任务状态失败: 无效响应")
        except Exception as e:
            log_exception(logger, e, f"获取SQLMap任务状态异常: {task_id}")
        
        return None
    
    def get_data(self, task_id):
        """获取扫描结果"""
        try:
            url = f"{self.api_url}/scan/{task_id}/data"
            response = http_get(url)
            if response and response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取SQLMap扫描结果失败: 无效响应")
        except Exception as e:
            log_exception(logger, e, f"获取SQLMap扫描结果异常: {task_id}")
        
        return None
    
    def delete_task(self, task_id):
        """删除任务"""
        try:
            url = f"{self.api_url}/task/{task_id}/delete"
            response = http_get(url)
            if response and response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info(f"删除SQLMap任务成功: {task_id}")
                    return True
                else:
                    logger.error(f"删除SQLMap任务失败: {data.get('message', '未知错误')}")
            else:
                logger.error(f"删除SQLMap任务失败: 无效响应")
        except Exception as e:
            log_exception(logger, e, f"删除SQLMap任务异常: {task_id}")
        
        return False
    
    def scan_url(self, url, callback=None):
        """扫描单个URL
        
        Args:
            url: 要扫描的URL
            callback: 扫描完成后的回调函数，接收两个参数(url, result)
            
        Returns:
            扫描结果或None（如果失败）
        """
        logger.info(f"开始扫描URL: {url}")
        
        # 创建任务
        task_id = self.create_task()
        if not task_id:
            logger.error(f"无法创建任务，跳过URL: {url}")
            return None
        
        # 设置选项
        options = {
            "url": url,
            "threads": SQLMAP_THREADS,
            "technique": "BEUQS",
            "crawl": 2,
            "randomAgent": True,
            "timeout": SQLMAP_TIMEOUT,
            "batch": True,
            "isDba": True,
            "dbs": True,
            "level": SQLMAP_LEVEL,
            "risk": SQLMAP_RISK,
            "forms": True
        }
        
        if not self.set_options(task_id, options):
            logger.error(f"无法设置选项，跳过URL: {url}")
            self.delete_task(task_id)
            return None
        
        # 开始扫描
        if not self.start_scan(task_id):
            logger.error(f"无法启动扫描，跳过URL: {url}")
            self.delete_task(task_id)
            return None
        
        # 等待扫描完成
        while True:
            status = self.get_status(task_id)
            if status == "running":
                logger.info(f"扫描中: {url}")
                time.sleep(5)
            else:
                break
        
        # 获取结果
        result = self.get_data(task_id)
        
        # 处理结果
        is_vulnerable = False
        if result:
            data = result.get("data", [])
            if data:
                is_vulnerable = True
                logger.warning(f"发现SQL注入漏洞: {url}")
            else:
                logger.info(f"未发现SQL注入漏洞: {url}")
        
        # 删除任务
        self.delete_task(task_id)
        
        # 执行回调
        if callback and callable(callback):
            callback(url, result)
        
        return result

# 异步SQLMap客户端
class AsyncSQLMapClient:
    """异步SQLMap API客户端"""
    
    def __init__(self):
        self.client = SQLMapClient()
    
    async def scan_url(self, url, callback=None):
        """异步扫描单个URL"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.client.scan_url(url, callback)
        )
    
    async def scan_urls(self, urls, max_concurrent=5, callback=None):
        """异步扫描多个URL
        
        Args:
            urls: URL列表
            max_concurrent: 最大并发数
            callback: 每个URL扫描完成后的回调函数
            
        Returns:
            结果字典，键为URL，值为扫描结果
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def scan_with_semaphore(url):
            async with semaphore:
                result = await self.scan_url(url, callback)
                results[url] = result
                return result
        
        tasks = [scan_with_semaphore(url) for url in urls]
        await asyncio.gather(*tasks)
        
        return results 