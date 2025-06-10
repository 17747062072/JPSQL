import requests
import os
from dotenv import load_dotenv
import time
from urllib.parse import urlparse
import base64

# 加载 API KEY
load_dotenv()

FOFA_EMAIL = os.getenv("FOFA_EMAIL")
FOFA_KEY = os.getenv("FOFA_KEY")
SHODAN_KEY = os.getenv("SHODAN_KEY")

# 搜索关键词：日本 + SQL注入敏感参数
keywords = [
    "id=", "uid=", "pid=", "cat=", "cid=", "aid=", "page=",
    "newsid=", "item=", "ref=", "type=", "doc=", "vid=",
    "post=", "user=", "act=", "id[]="
]

# 总共要采集的目标数量
MAX_TARGETS = 200
seen = set()

def save_url_if_new(url, filename="mubiao.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(url + "\n")
    print(f"[+] 保存目标: {url}")

def is_valid_sql_url(url):
    return any(kw in url for kw in keywords)

def is_jp_domain(url):
    domain = urlparse(url).netloc
    return domain.endswith(".jp")

def fofa_search():
    print("[*] FOFA 搜索中...")
    base_url = "https://fofa.info/api/v1/search/all"
    query = 'site=".jp" && (url="id=" || url="uid=" || url="pid=" || url="cat=" || url="cid=" || url="aid=")'
    qbase64 = base64.b64encode(query.encode()).decode()
    params = {
        "email": FOFA_EMAIL,
        "key": FOFA_KEY,
        "qbase64": qbase64,
        "fields": "host",
        "size": 100,
        "page": 1
    }

    while len(seen) < MAX_TARGETS:
        try:
            response = requests.get(base_url, params=params)
            if response.status_code != 200:
                print("[!] FOFA API 错误：", response.text)
                break

            data = response.json()
            results = data.get("results", [])
            if not results:
                break

            for row in results:
                url = row[0]
                if is_valid_sql_url(url) and url not in seen and is_jp_domain(url):
                    save_url_if_new(url)
                    seen.add(url)
                    if len(seen) >= MAX_TARGETS:
                        return

            params["page"] += 1
            time.sleep(1)
        except Exception as e:
            print("[!] FOFA 异常：", e)
            break

def shodan_search():
    print("[*] Shodan 搜索中...")
    base_url = "https://api.shodan.io/shodan/host/search"
    query = "http.html:.jp id="  # HTML 内容中包含日本域名 + SQL关键词
    page = 1

    while len(seen) < MAX_TARGETS:
        try:
            params = {
                "key": SHODAN_KEY,
                "query": query,
                "page": page
            }

            response = requests.get(base_url, params=params)
            if response.status_code != 200:
                print("[!] Shodan API 错误：", response.text)
                break

            data = response.json()
            matches = data.get("matches", [])
            if not matches:
                break

            for match in matches:
                ip_str = match.get("ip_str", "")
                port = match.get("port", 80)
                url = f"http://{ip_str}:{port}"
                if url not in seen and is_valid_sql_url(url):
                    save_url_if_new(url)
                    seen.add(url)
                    if len(seen) >= MAX_TARGETS:
                        return

            page += 1
            time.sleep(1)
        except Exception as e:
            print("[!] Shodan 异常：", e)
            break

if __name__ == "__main__":
    print("[*] 开始采集 SQL 注入可疑日本目标（最多 200 条）...\n")
    fofa_search()
    if len(seen) < MAX_TARGETS:
        shodan_search()

    print(f"\n[+] 完成，已采集目标数: {len(seen)} 条")
