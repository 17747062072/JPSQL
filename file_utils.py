import os
import sys
import json
from datetime import datetime

# 导入配置和工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, TARGETS_FILE, RESULTS_FILE, VULN_FILE
from utils.logger import get_logger

logger = get_logger("file_utils")

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_urls_from_file(file_path):
    """从文件中读取URL列表
    
    Args:
        file_path: 文件路径
        
    Returns:
        URL列表
    """
    urls = []
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            logger.info(f"从 {file_path} 读取了 {len(urls)} 个URL")
        else:
            logger.warning(f"文件不存在: {file_path}")
    except Exception as e:
        logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
    
    return urls

def write_urls_to_file(urls, file_path, mode='w'):
    """将URL列表写入文件
    
    Args:
        urls: URL列表
        file_path: 文件路径
        mode: 写入模式 ('w'覆盖, 'a'追加)
        
    Returns:
        是否写入成功
    """
    try:
        with open(file_path, mode, encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")
        logger.info(f"已将 {len(urls)} 个URL写入 {file_path}")
        return True
    except Exception as e:
        logger.error(f"写入文件失败: {file_path}, 错误: {str(e)}")
        return False

def append_url_to_file(url, file_path):
    """向文件追加单个URL
    
    Args:
        url: URL
        file_path: 文件路径
        
    Returns:
        是否写入成功
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")
        logger.debug(f"已将URL追加到 {file_path}: {url}")
        return True
    except Exception as e:
        logger.error(f"追加URL失败: {file_path}, 错误: {str(e)}")
        return False

def save_result_to_file(url, result, file_path=RESULTS_FILE):
    """保存扫描结果到文件
    
    Args:
        url: 扫描的URL
        result: 扫描结果
        file_path: 文件路径
        
    Returns:
        是否保存成功
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 格式化结果
        if isinstance(result, dict):
            result_str = json.dumps(result, ensure_ascii=False)
        else:
            result_str = str(result)
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] URL: {url}\n")
            f.write(f"{result_str}\n")
            f.write("-" * 80 + "\n")
        
        logger.info(f"已保存扫描结果到 {file_path}: {url}")
        return True
    except Exception as e:
        logger.error(f"保存扫描结果失败: {file_path}, 错误: {str(e)}")
        return False

def save_vulnerability(url, result, file_path=VULN_FILE):
    """保存漏洞信息到文件
    
    Args:
        url: 发现漏洞的URL
        result: 扫描结果
        file_path: 文件路径
        
    Returns:
        是否保存成功
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 格式化结果
        if isinstance(result, dict):
            result_str = json.dumps(result, ensure_ascii=False, indent=2)
        else:
            result_str = str(result)
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] 发现漏洞: {url}\n")
            f.write(f"{result_str}\n")
            f.write("=" * 80 + "\n\n")
        
        logger.warning(f"已保存漏洞信息到 {file_path}: {url}")
        return True
    except Exception as e:
        logger.error(f"保存漏洞信息失败: {file_path}, 错误: {str(e)}")
        return False

def load_progress(file_name):
    """加载进度文件
    
    Args:
        file_name: 进度文件名
        
    Returns:
        进度数据字典
    """
    progress_file = os.path.join(OUTPUT_DIR, file_name)
    try:
        if os.path.exists(progress_file):
            with open(progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.info(f"进度文件不存在: {progress_file}")
    except Exception as e:
        logger.error(f"加载进度失败: {progress_file}, 错误: {str(e)}")
    
    return {}

def save_progress(data, file_name):
    """保存进度文件
    
    Args:
        data: 进度数据字典
        file_name: 进度文件名
        
    Returns:
        是否保存成功
    """
    progress_file = os.path.join(OUTPUT_DIR, file_name)
    try:
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存进度到 {progress_file}")
        return True
    except Exception as e:
        logger.error(f"保存进度失败: {progress_file}, 错误: {str(e)}")
        return False 