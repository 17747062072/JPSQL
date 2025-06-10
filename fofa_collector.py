import sys
import os
import time
import base64
import asyncio

# 导入配置和工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FOFA_EMAIL, FOFA_KEY, MAX_TARGETS, SQLI_PARAMS
from utils.logger import get_logger
from utils.http_client import http_get
from utils.url_tools import is_valid_url, is_jp_domain, has_sqli_param
from utils.file_utils import append_url_to_file, save_progress

logger = get_logger("fofa_collector")

class FofaCollector:
    """FOFA搜索收集器"""
    
    def __init__(self, email=FOFA_EMAIL, key=FOFA_KEY, output_file="output/fofa_urls.txt"):
        self.email = email
        self.key = key
        self.output_file = output_file
        self.seen_urls = set()
        self.collected_count = 0
        self.max_targets = MAX_TARGETS
    
    def fofa_search(self, query, page=1, size=100):
        """执行FOFA搜索
        
        Args:
            query: 搜索关键词
            page: 页码
            size: 每页结果数
            
        Returns:
            搜索结果列表
        """
        base_url = "https://fofa.info/api/v1/search/all"
        
        # Base64编码查询
        qbase64 = base64.b64encode(query.encode()).decode()
        
        params = {
            "email": self.email,
            "key": self.key,
            "qbase64": qbase64,
            "fields": "host,ip,port,protocol",
            "size": size,
            "page": page
        }
        
        try:
            response = http_get(base_url, params=params)
            if response and response.status_code == 200:
                data = response.json()
                if data.get("error"):
                    logger.error(f"FOFA API错误: {data.get('errmsg')}")
                    return []
                
                return data.get("results", [])
            else:
                logger.error(f"FOFA搜索请求失败: {response.status_code if response else 'No response'}")
        except Exception as e:
            logger.error(f"FOFA搜索异常: {str(e)}")
        
        return []
    
    def process_results(self, results):
        """处理搜索结果
        
        Args:
            results: 搜索结果列表
            
        Returns:
            处理后的URL列表
        """
        processed = []
        
        for row in results:
            try:
                host = row[0]
                protocol = row[3] if len(row) > 3 else "http"
                
                # 构建URL
                url = f"{protocol}://{host}"
                
                # 检查URL是否有效且为日本域名
                if is_valid_url(url) and is_jp_domain(url) and url not in self.seen_urls:
                    self.seen_urls.add(url)
                    processed.append(url)
                    
                    # 保存URL
                    append_url_to_file(url, self.output_file)
                    self.collected_count += 1
                    
                    logger.info(f"收集到新URL: {url}")
            except Exception as e:
                logger.debug(f"处理结果异常: {str(e)}")
        
        return processed
    
    def collect(self, queries, max_pages=10):
        """收集URL
        
        Args:
            queries: 搜索关键词列表
            max_pages: 每个关键词最大页数
            
        Returns:
            收集到的URL列表
        """
        logger.info(f"开始FOFA搜索收集，目标数量: {self.max_targets}")
        
        for query in queries:
            logger.info(f"搜索关键词: {query}")
            page = 1
            
            while self.collected_count < self.max_targets and page <= max_pages:
                logger.info(f"查询页码: {page}")
                results = self.fofa_search(query, page=page)
                
                if not results:
                    logger.warning(f"关键词 '{query}' 无更多结果")
                    break
                
                processed = self.process_results(results)
                logger.info(f"本轮新增结果: {len(processed)}, 总计: {self.collected_count}")
                
                if len(processed) == 0:
                    logger.warning(f"关键词 '{query}' 无有效结果，跳过")
                    break
                
                if self.collected_count >= self.max_targets:
                    logger.info(f"已达到目标数量: {self.max_targets}")
                    break
                
                page += 1
                time.sleep(2)  # 避免API限制
        
        logger.info(f"FOFA搜索收集完成，共收集URL: {self.collected_count}")
        return list(self.seen_urls)

def generate_queries():
    """生成FOFA搜索关键词"""
    queries = []
    
    # 基础查询：日本域名
    base_query = 'domain=".jp" && country="JP"'
    
    # 添加SQL注入参数
    for param in SQLI_PARAMS:
        queries.append(f'{base_query} && body="{param}="')
    
    # 添加常见CMS
    cms_list = ["WordPress", "Joomla", "Drupal"]
    for cms in cms_list:
        queries.append(f'{base_query} && app="{cms}"')
    
    return queries

def main():
    """主函数"""
    # 检查API密钥
    if not FOFA_EMAIL or not FOFA_KEY:
        logger.error("FOFA API配置不完整，请在.env文件中设置FOFA_EMAIL和FOFA_KEY")
        return
    
    # 生成搜索关键词
    queries = generate_queries()
    
    # 创建收集器
    collector = FofaCollector()
    
    # 收集URL
    urls = collector.collect(queries, max_pages=5)
    
    # 保存统计信息
    stats = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_collected": len(urls),
        "queries": queries
    }
    save_progress(stats, "fofa_stats.json")
    
    logger.info(f"共收集URL: {len(urls)}")

if __name__ == "__main__":
    main() 