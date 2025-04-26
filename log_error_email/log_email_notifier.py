# 分析错误日志文件并发送邮件
# 需修改日志记录的格式
# 日志格式：时间|错误代码|错误信息|文件地址|行数 也可以根据现有的日志格式修改代码

import smtplib
import time
import hashlib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itertools import zip_longest

# 日志目录地址
log_path = '项目地址'

# 日志目录列表 根据需求添加
log_dirs = [
    log_path+'/api/log',
    log_path+'/admin/log',
    log_path+'/index/log'
]

# 邮箱服务器配置
smtp_server = 'smtp.sina.cn'
smtp_port = 587
# 发送邮件的邮箱
send_email = ''
# 授权码
send_pssword = ''
# 接收邮件的邮箱
receive_email = ''

# 存储已发送错误的哈希值的文件路径
send_error_file_path = '/www/wwwroot/python/log_error_email/log/'
# 已发送错误的哈希值文件名称
send_error_file_name = 'sent_error.txt'

# 计算错误的哈希值
def get_error_hash(error):
    return hashlib.md5(error.encode()).hexdigest()

# 获取年月日拼接文件路径
def get_file_path():
    year = time.strftime('%Y', time.localtime())
    month = time.strftime('%m', time.localtime())
    # 只返回哈希文件路径
    return os.path.join(send_error_file_path, year, month, send_error_file_name)

# 加载已发送错误的哈希值
def load_sent_errors(send_error_file):
    # 如果文件不存在时创建 多个目录
    if os.path.exists(send_error_file):
        with open(send_error_file,'r') as file:
            return set(file.read().splitlines())
    else:
        os.makedirs(os.path.dirname(send_error_file), exist_ok=True)
    return set()

# 保存已发送错误的哈希值
def save_sent_errors(send_error_file, send_errors):
    with open(send_error_file, 'w') as f:
        for error in send_errors:
            f.write(f"{error}\n")

# 发送邮件
def send_email_notify(title, body):
    msg = MIMEMultipart()
    msg['From'] = send_email
    msg['To'] = receive_email
    msg['subject'] = title
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP(smtp_server,smtp_port) as server:
            server.starttls()
            server.login(send_email, send_pssword)
            server.sendmail(send_email, receive_email, msg.as_string())
    except Exception as e:
        print(f"发送邮件失败: {e}")



# 获取所有日志文件路径
def get_all_log_file_paths():
    year = time.strftime('%Y', time.localtime())
    month = time.strftime('%m', time.localtime())
    day = time.strftime('%d', time.localtime())
    log_files = []
    for log_dir in log_dirs:
        log_file = os.path.join(log_dir, year+month, day+'.log')
        log_files.append(log_file)
    return log_files

# 读取多个日志文件并分析错误
def get_log_error_multi(log_file_paths, send_errors):
    new_errors = []
    for log_file_path in log_file_paths:
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path,'r',encoding='utf-8') as log_file:
                    for line in log_file:
                        error_message = line.strip()
                        # 错误信息格式：错误类型|错误信息|错误时间|错误文件|错误行数 根据需求修改
                        error_message_array = error_message.split('|')
                        if len(error_message_array) < 5:
                            continue
                        error_hash = get_error_hash(error_message_array[2]+error_message_array[3]+error_message_array[4])
                        if error_hash not in send_errors:
                            new_errors.append(error_message_array)
                            send_errors.add(error_hash)
            except Exception as e:
                print(f"读取日志文件失败: {log_file_path} 错误: {e}")
    return new_errors

# 记录并发送错误（多日志文件版本）
def check_and_send_error_multi(send_error_file, log_file_paths, send_errors):
    new_errors = get_log_error_multi(log_file_paths, send_errors)
    if new_errors:
        title = '错误通知'
        body = ''
        for error in new_errors:
            for label, value in zip_longest(['时间', '错误代码', '错误信息', '文件地址', '行数'],error, fillvalue='无'):
                body += f"{label}：{value}\n"
            body += "\n\n"
        send_email_notify(title, body)
        save_sent_errors(send_error_file, send_errors)

if __name__ == '__main__':
    # Get the hash file path only
    hash_error_file_path = get_file_path()
    log_file_paths = get_all_log_file_paths()
    send_errors = load_sent_errors(hash_error_file_path)
    check_and_send_error_multi(hash_error_file_path, log_file_paths, send_errors)