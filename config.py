import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API密钥
GOOGLE_API_KEY = os.getenv("GOOGLE_API")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "65305f4848f504fee")
FOFA_EMAIL = os.getenv("FOFA_EMAIL")
FOFA_KEY = os.getenv("FOFA_KEY")
SHODAN_KEY = os.getenv("SHODAN_KEY")

# 邮件配置
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

# SQLMap API配置
SQLMAP_API_URL = os.getenv("SQLMAP_API_URL", "http://127.0.0.1:8775")
SQLMAP_THREADS = int(os.getenv("SQLMAP_THREADS", "10"))
SQLMAP_TIMEOUT = int(os.getenv("SQLMAP_TIMEOUT", "20"))
SQLMAP_LEVEL = int(os.getenv("SQLMAP_LEVEL", "5"))
SQLMAP_RISK = int(os.getenv("SQLMAP_RISK", "3"))

# 扫描配置
MAX_TARGETS = int(os.getenv("MAX_TARGETS", "200"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

# 文件路径配置
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
TARGETS_FILE = os.path.join(OUTPUT_DIR, "targets.txt")
RESULTS_FILE = os.path.join(OUTPUT_DIR, "results.txt")
VULN_FILE = os.path.join(OUTPUT_DIR, "vulnerabilities.txt")

# SQL注入关键词
SQLI_PARAMS = [
    "id", "uid", "userid", "page", "cat", "category", "item", "product", "pid",
    "article", "view", "news", "type", "sort", "tid", "mid", "gid", "search", 
    "q", "query", "newsid", "item", "ref", "doc", "vid", "post", "user", 
    "act", "id[]", "cid", "aid"
]

# 黑名单域名
BLACKLIST_DOMAINS = [
    "good-apps.jp", "senetwork.co.jp", "app.adjust.com",
    "apps.apple.com", "play.google.com", "bit.ly",
    "t.co", "smarturl.it", "lnk.to"
]

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True) 