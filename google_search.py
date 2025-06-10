import os
import requests
from dotenv import load_dotenv
import time
from urllib.parse import urlparse, urlsplit, parse_qs, urlunsplit

# 加载环境变量
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API")
SEARCH_ENGINE_ID = '65305f4848f504fee'

# 可疑参数关键词（常见 SQL 注入点）
keywords = [
    "newsid=", "item=", "ref=", "type=", "doc=", "vid=",
    "post=", "user=", "act=", "id[]="
]

# 跳转平台黑名单域名
blacklist_domains = [
    "good-apps.jp", "senetwork.co.jp", "app.adjust.com",
    "apps.apple.com", "play.google.com", "bit.ly",
    "t.co", "smarturl.it", "lnk.to"
]

# 跳转参数关键词
redirect_keywords = ["url=", "redirect=", "redir=", "goto="]

def google_search(query, num_results=10, start_index=1):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}&num={num_results}&start={start_index}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('items', [])
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Google search 请求失败: {e}")
        return []

def is_blacklisted(url):
    domain = urlparse(url).netloc
    return any(bad in domain for bad in blacklist_domains)

def is_redirect_link(url):
    return any(param in url.lower() for param in redirect_keywords)

def clean_url(url):
    """去除跳转参数，只保留主业务逻辑部分"""
    parsed = urlsplit(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    cleaned_qs = {k: v for k, v in qs.items() if k.lower() not in ["url", "redirect", "redir", "goto"]}
    new_query = '&'.join(f"{k}={v[0]}" for k, v in cleaned_qs.items())
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))

def normalize_url(url):
    """提取用于去重的唯一标识（不含参数，只保留结构）"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def filter_urls(items, seen_urls, seen_structures):
    results = []
    for item in items:
        url = item.get('link', '')
        if any(k in url for k in keywords) and not is_blacklisted(url) and not is_redirect_link(url):
            cleaned = clean_url(url)
            normalized = normalize_url(cleaned)
            if normalized not in seen_structures:
                results.append(cleaned)
                seen_urls.add(cleaned)
                seen_structures.add(normalized)
                save_url_if_new(cleaned)
    return results

def save_url_if_new(url, filename="filtered_urls.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(url + "\n")
    print(f"[+] 实时保存: {url}")

def get_all_results(query_list, total_results=100, max_requests=10):
    collected_urls = set()
    collected_structures = set()
    for q in query_list:
        print(f"\n[INFO] 查询关键词: {q}")
        start_index = 1
        request_count = 0

        while len(collected_urls) < total_results and request_count < max_requests:
            print(f" -> 分页查询 {start_index} 到 {start_index + 9}")
            items = google_search(q, num_results=10, start_index=start_index)

            if not items:
                print(" [!] 无结果，跳过")
                break

            filtered = filter_urls(items, collected_urls, collected_structures)
            print(f" [+] 本轮新增结果: {len(filtered)}")

            if len(collected_urls) >= total_results:
                break

            start_index += 10
            request_count += 1

            if request_count % 3 == 0:
                print("[WAIT] 避免配额限制，等待 30 秒...")
                time.sleep(30)
            else:
                time.sleep(2)

    return list(collected_urls)

if __name__ == "__main__":
    queries = [f"site:.jp inurl:{k}" for k in keywords]
    total_results = 1000
    max_requests_per_query = 5

    print("[*] 开始 Google SQL 注入目标采集...")
    results = get_all_results(queries, total_results=total_results, max_requests=max_requests_per_query)

    print(f"\n[+] 共采集有效目标: {len(results)} 条")
