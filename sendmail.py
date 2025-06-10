import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

my_sender = os.getenv("EMAIL_USER")
my_pass = os.getenv("EMAIL_PASS")
my_user = os.getenv("EMAIL_TO")

def mail(url, data):
    title = "发现漏洞：" + url
    msg = MIMEText(str(data), 'plain', 'utf-8')
    msg['From'] = formataddr(["自动化系统", my_sender])
    msg['To'] = formataddr(["收件人", my_user])
    msg['Subject'] = title

    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(my_sender, my_pass)
        server.sendmail(my_sender, [my_user], msg.as_string())
        server.quit()
        print("[+] 邮件已发送:", url)
    except Exception as e:
        print("[-] 邮件发送失败:", str(e))
