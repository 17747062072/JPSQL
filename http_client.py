import sys
import os
import requests
import time
import random
from requests.exceptions import RequestException
import aiohttp
import asyncio

# 导入配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_TIMEOUT
from utils.logger import get_logger, log_exception

logger = get_logger("http_client")

# 用户代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
]

def get_random_user_agent():
    """获取随机用户代理"""
    return random.choice(USER_AGENTS)

def get_headers():
    """获取HTTP请求头"""
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

def http_get(url, timeout=REQUEST_TIMEOUT, retries=3, delay=1):
    """发送HTTP GET请求
    
    Args:
        url: 请求URL
        timeout: 超时时间（秒）
        retries: 重试次数
        delay: 重试延迟（秒）
        
    Returns:
        响应对象或None（如果失败）
    """
    headers = get_headers()
    
    for attempt in range(retries):
        try:
            logger.debug(f"GET请求: {url} (尝试 {attempt+1}/{retries})")
            response = requests.get(
                url, 
                headers=headers, 
                timeout=timeout,
                verify=False  # 忽略SSL错误
            )
            return response
        except RequestException as e:
            log_exception(logger, e, f"GET请求失败: {url}")
            if attempt < retries - 1:
                time.sleep(delay)
    
    return None

def http_post(url, data=None, json=None, timeout=REQUEST_TIMEOUT, retries=3, delay=1):
    """发送HTTP POST请求
    
    Args:
        url: 请求URL
        data: 表单数据
        json: JSON数据
        timeout: 超时时间（秒）
        retries: 重试次数
        delay: 重试延迟（秒）
        
    Returns:
        响应对象或None（如果失败）
    """
    headers = get_headers()
    
    for attempt in range(retries):
        try:
            logger.debug(f"POST请求: {url} (尝试 {attempt+1}/{retries})")
            response = requests.post(
                url, 
                headers=headers, 
                data=data,
                json=json,
                timeout=timeout,
                verify=False  # 忽略SSL错误
            )
            return response
        except RequestException as e:
            log_exception(logger, e, f"POST请求失败: {url}")
            if attempt < retries - 1:
                time.sleep(delay)
    
    return None

# 异步HTTP客户端
async def async_get(url, timeout=REQUEST_TIMEOUT, retries=3, delay=1):
    """异步发送HTTP GET请求
    
    Args:
        url: 请求URL
        timeout: 超时时间（秒）
        retries: 重试次数
        delay: 重试延迟（秒）
        
    Returns:
        响应文本或None（如果失败）
    """
    headers = get_headers()
    
    for attempt in range(retries):
        try:
            logger.debug(f"异步GET请求: {url} (尝试 {attempt+1}/{retries})")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=headers, 
                    timeout=timeout,
                    ssl=False  # 忽略SSL错误
                ) as response:
                    return await response.text()
        except Exception as e:
            log_exception(logger, e, f"异步GET请求失败: {url}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    
    return None

async def async_post(url, data=None, json=None, timeout=REQUEST_TIMEOUT, retries=3, delay=1):
    """异步发送HTTP POST请求
    
    Args:
        url: 请求URL
        data: 表单数据
        json: JSON数据
        timeout: 超时时间（秒）
        retries: 重试次数
        delay: 重试延迟（秒）
        
    Returns:
        响应文本或None（如果失败）
    """
    headers = get_headers()
    
    for attempt in range(retries):
        try:
            logger.debug(f"异步POST请求: {url} (尝试 {attempt+1}/{retries})")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    headers=headers, 
                    data=data,
                    json=json,
                    timeout=timeout,
                    ssl=False  # 忽略SSL错误
                ) as response:
                    return await response.text()
        except Exception as e:
            log_exception(logger, e, f"异步POST请求失败: {url}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    
    return None 