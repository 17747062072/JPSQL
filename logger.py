import logging
import os
import sys
from datetime import datetime
import traceback

# 导入配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR

# 确保日志目录存在
LOG_DIR = os.path.join(OUTPUT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 创建日志文件名，包含日期
log_filename = os.path.join(LOG_DIR, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# 配置日志格式
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 创建文件处理器
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setFormatter(log_format)

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)

def get_logger(name):
    """获取一个配置好的日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 避免重复添加处理器
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def log_exception(logger, e, message="发生异常"):
    """记录异常详情"""
    logger.error(f"{message}: {str(e)}")
    logger.debug(traceback.format_exc())

# 创建默认日志记录器
logger = get_logger("jpsql") 