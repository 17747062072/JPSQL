import sys
import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# 导入配置和工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EMAIL_USER, EMAIL_PASS, EMAIL_TO
from utils.logger import get_logger, log_exception

logger = get_logger("notifier")

class EmailNotifier:
    """邮件通知类"""
    
    def __init__(self, sender=EMAIL_USER, password=EMAIL_PASS, receiver=EMAIL_TO):
        self.sender = sender
        self.password = password
        self.receiver = receiver
    
    def send_mail(self, subject, content, content_type='plain'):
        """发送邮件
        
        Args:
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型（'plain' 或 'html'）
            
        Returns:
            是否发送成功
        """
        if not all([self.sender, self.password, self.receiver]):
            logger.error("邮件配置不完整，无法发送邮件")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr(["自动化扫描系统", self.sender])
            msg['To'] = formataddr(["管理员", self.receiver])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, content_type, 'utf-8'))
            
            server = smtplib.SMTP_SSL("smtp.qq.com", 465)
            server.login(self.sender, self.password)
            server.sendmail(self.sender, [self.receiver], msg.as_string())
            server.quit()
            
            logger.info(f"邮件发送成功: {subject}")
            return True
        except Exception as e:
            log_exception(logger, e, "邮件发送失败")
            return False
    
    def notify_vulnerability(self, url, result):
        """发送漏洞通知
        
        Args:
            url: 发现漏洞的URL
            result: SQLMap扫描结果
            
        Returns:
            是否发送成功
        """
        subject = f"[安全警报] 发现SQL注入漏洞: {url}"
        
        # 格式化结果
        if isinstance(result, dict):
            content = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            content = str(result)
        
        content = f"URL: {url}\n\n详细信息:\n{content}"
        
        return self.send_mail(subject, content)
    
    def notify_scan_complete(self, stats):
        """发送扫描完成通知
        
        Args:
            stats: 扫描统计信息
            
        Returns:
            是否发送成功
        """
        subject = "[扫描完成] SQL注入扫描任务已完成"
        
        content = "扫描统计信息:\n"
        content += f"- 总URL数: {stats.get('total', 0)}\n"
        content += f"- 成功扫描: {stats.get('scanned', 0)}\n"
        content += f"- 发现漏洞: {stats.get('vulnerable', 0)}\n"
        content += f"- 扫描失败: {stats.get('failed', 0)}\n"
        
        if stats.get('vulnerable_urls'):
            content += "\n发现漏洞的URL:\n"
            for url in stats.get('vulnerable_urls', []):
                content += f"- {url}\n"
        
        return self.send_mail(subject, content)

# 创建默认通知器
notifier = EmailNotifier() 