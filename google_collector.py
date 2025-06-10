import sys
import os
import time
import asyncio
from urllib.parse import urlparse, parse_qs

# 导入配置和工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_API_KEY, SEARCH_ENGINE_ID, SQLI_PARAMS, MAX_TARGETS
from utils.logger import get_logger
from utils.http_client import http_get
from utils.url_tools import is_blacklisted, clean_url, normalize_url, has_sqli_param
from utils.file_utils import append_url_to_file, write_urls_to_file, save_progress

logger = get_logger("google_collector")

class GoogleCollector:
    """Google搜索收集器"""
    
    def __init__(self, api_key=GOOGLE_API_KEY, cx=SEARCH_ENGINE_ID, output_file="output/google_urls.txt"):
        self.api_key = api_key
        self.cx = cx
        self.output_file = output_file
        self.seen_urls = set()
        self.seen_structures = set()
        self.collected_count = 0
        self.max_targets = MAX_TARGETS
    
    def google_search(self, query, num_results=10, start_index=1):
        """执行Google搜索
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            start_index: 起始索引
            
        Returns:
            搜索结果列表
        """
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={self.api_key}&cx={self.cx}&num={num_results}&start={start_index}"
        
        try:
            response = http_get(url)
            if response and response.status_code == 200:
                data = response.json()
                return data.get('items', [])
            else:
                logger.error(f"Google搜索请求失败: {response.status_code if response else 'No response'}")
        except Exception as e:
            logger.error(f"Google搜索异常: {str(e)}")
        
        return []
    
    def filter_urls(self, items):
        """过滤搜索结果，提取有效URL
        
        Args:
            items: 搜索结果项列表
            
        Returns:
            过滤后的URL列表
        """
        results = []
        
        for item in items:
            url = item.get('link', '')
            
            # 检查URL是否包含SQL注入参数
            if has_sqli_param(url) and not is_blacklisted(url):
                cleaned = clean_url(url)
                normalized = normalize_url(cleaned)
                
                # 去重
                if normalized not in self.seen_structures:
                    results.append(cleaned)
                    self.seen_urls.add(cleaned)
                    self.seen_structures.add(normalized)
                    
                    # 保存URL
                    append_url_to_file(cleaned, self.output_file)
                    self.collected_count += 1
                    
                    logger.info(f"收集到新URL: {cleaned}")
        
        return results
    
    def collect(self, queries, max_requests_per_query=5):
        """收集URL
        
        Args:
            queries: 搜索关键词列表
            max_requests_per_query: 每个关键词最大请求次数
            
        Returns:
            收集到的URL列表
        """
        logger.info(f"开始Google搜索收集，目标数量: {self.max_targets}")
        
        for query in queries:
            logger.info(f"搜索关键词: {query}")
            start_index = 1
            request_count = 0
            
            while self.collected_count < self.max_targets and request_count < max_requests_per_query:
                logger.info(f"分页查询: {start_index} 到 {start_index + 9}")
                items = self.google_search(query, num_results=10, start_index=start_index)
                
                if not items:
                    logger.warning(f"关键词 '{query}' 无更多结果")
                    break
                
                filtered = self.filter_urls(items)
                logger.info(f"本轮新增结果: {len(filtered)}, 总计: {self.collected_count}")
                
                if self.collected_count >= self.max_targets:
                    logger.info(f"已达到目标数量: {self.max_targets}")
                    break
                
                start_index += 10
                request_count += 1
                
                # 避免API限制
                if request_count % 3 == 0:
                    logger.info("避免配额限制，等待30秒...")
                    time.sleep(30)
                else:
                    time.sleep(2)
        
        logger.info(f"Google搜索收集完成，共收集URL: {self.collected_count}")
        return list(self.seen_urls)

def generate_queries():
    """生成搜索关键词"""
    queries = []
    
    # 日本站点 + SQL注入参数
    for param in SQLI_PARAMS:
        queries.append(f"site:.jp inurl:{param}")
    
    return queries

def main():
    """主函数"""
    # 生成搜索关键词
    queries = generate_queries()
    
    # 创建收集器
    collector = GoogleCollector()
    
    # 收集URL
    urls = collector.collect(queries, max_requests_per_query=5)
    
    # 保存统计信息
    stats = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_collected": len(urls),
        "queries": queries
    }
    save_progress(stats, "google_stats.json")
    
    logger.info(f"共收集URL: {len(urls)}")

if __name__ == "__main__":
    main() 