import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
import threading

# SQL 注入关键词
sqli_keywords = [
    "id", "uid", "userid", "page", "cat", "category", "item", "product", "pid",
    "article", "view", "news", "type", "sort", "tid", "mid", "gid", "search", "q", "query"
]

lock = threading.Lock()
seen_domains = set()  # 用于域名去重

# 判断 URL 是否含有可疑参数
def is_sqli_param(query):
    params = parse_qs(query)
    for param in params:
        if param.lower() in sqli_keywords:
            return True
    return False

# 检查 URL
def check_url(base_url):
    try:
        print(f"[*] Checking: {base_url}")
        response = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # 查找所有 a 标签
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            if parsed.query and is_sqli_param(parsed.query):
                domain = parsed.netloc
                with lock:
                    if domain not in seen_domains:
                        seen_domains.add(domain)
                        with open("filtered_urls.txt", "a", encoding="utf-8") as f:
                            f.write(full_url + "\n")
                        print(f"[+] Saved (new domain): {full_url}")
                return  # 每个域名只记录一个可疑链接，发现就退出循环

        # 查找 GET 表单
        for form in soup.find_all("form", action=True):
            method = form.get("method", "get").lower()
            if method == "get":
                action = form["action"]
                full_url = urljoin(base_url, action)
                parsed = urlparse(full_url)
                if parsed.query and is_sqli_param(parsed.query):
                    domain = parsed.netloc
                    with lock:
                        if domain not in seen_domains:
                            seen_domains.add(domain)
                            with open("filtered_urls.txt", "a", encoding="utf-8") as f:
                                f.write(full_url + "\n")
                            print(f"[+] Saved (form): {full_url}")
                    return

        print(f"[-] No suspicious parameters in: {base_url}")

    except Exception as e:
        print(f"[!] Error checking {base_url}: {e}")

# 主程序
if __name__ == "__main__":
    with open("zhaocanshu.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(check_url, urls)
