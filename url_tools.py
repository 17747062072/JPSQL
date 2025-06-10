import re
import sys
import os
from urllib.parse import urlparse, parse_qs, urljoin, urlsplit, urlunsplit

# 导入配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SQLI_PARAMS, BLACKLIST_DOMAINS
from utils.logger import get_logger

logger = get_logger("url_tools")

def is_valid_url(url):
    """检查URL是否有效"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.debug(f"无效URL: {url}, 错误: {str(e)}")
        return False

def is_jp_domain(url):
    """检查是否为日本域名"""
    try:
        domain = urlparse(url).netloc
        return domain.endswith(".jp")
    except Exception as e:
        logger.debug(f"域名检查失败: {url}, 错误: {str(e)}")
        return False

def is_blacklisted(url):
    """检查URL是否在黑名单中"""
    try:
        domain = urlparse(url).netloc
        return any(bad in domain for bad in BLACKLIST_DOMAINS)
    except Exception as e:
        logger.debug(f"黑名单检查失败: {url}, 错误: {str(e)}")
        return False

def has_sqli_param(url):
    """检查URL是否包含SQL注入相关参数"""
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # 检查参数名是否在SQL注入关键词列表中
        for param in query_params:
            if param.lower() in SQLI_PARAMS:
                return True
                
        # 检查URL路径中是否包含SQL注入关键词
        for keyword in SQLI_PARAMS:
            if f"{keyword}=" in url:
                return True
                
        return False
    except Exception as e:
        logger.debug(f"参数检查失败: {url}, 错误: {str(e)}")
        return False

def normalize_url(url):
    """标准化URL（去除参数值，只保留结构）用于去重"""
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception as e:
        logger.debug(f"URL标准化失败: {url}, 错误: {str(e)}")
        return url

def clean_url(url):
    """清理URL，去除跳转参数"""
    try:
        parsed = urlsplit(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        
        # 移除跳转相关参数
        redirect_params = ["url", "redirect", "redir", "goto"]
        cleaned_qs = {k: v for k, v in qs.items() if k.lower() not in redirect_params}
        
        new_query = '&'.join(f"{k}={v[0]}" for k, v in cleaned_qs.items())
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))
    except Exception as e:
        logger.debug(f"URL清理失败: {url}, 错误: {str(e)}")
        return url

def extract_links_from_html(html, base_url):
    """从HTML中提取链接"""
    links = []
    try:
        # 简单的正则表达式匹配链接
        href_pattern = re.compile(r'href=["\'](.*?)["\']', re.IGNORECASE)
        for href in href_pattern.findall(html):
            try:
                full_url = urljoin(base_url, href)
                if is_valid_url(full_url):
                    links.append(full_url)
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"链接提取失败: {base_url}, 错误: {str(e)}")
    
    return links

def filter_urls(urls):
    """过滤URL列表，只保留有效且含SQL注入参数的URL"""
    filtered = []
    for url in urls:
        if (is_valid_url(url) and 
            has_sqli_param(url) and 
            not is_blacklisted(url)):
            filtered.append(url)
    return filtered 