import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_FROM, EMAIL_TO, EMAIL_SMTP, EMAIL_PORT, EMAIL_PASSWORD


def send(subject, html_file_path):
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_body = f.read()

    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

    print(f"邮件已发送至 {EMAIL_TO}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法: python3 send_email.py "邮件主题" /path/to/report.html')
        sys.exit(1)
    send(sys.argv[1], sys.argv[2])
