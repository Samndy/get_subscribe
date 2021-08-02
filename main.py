import os
import re
import smtplib
import sys
import time
from email.mime.text import MIMEText
from email.utils import formataddr

import feedparser
import requests

requests.packages.urllib3.disable_warnings()


ok_code = [200, 201, 202, 203, 204, 205, 206]


def write_log(content, level="INFO"):

    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    update_log = f"[{date_str}] [{level}] {content}\n"
    with open(f'./log/{time.strftime("%Y-%m", time.localtime(time.time()))}-update.log', 'a', encoding="utf-8") as f:
        f.write(update_log)

def get_mail():
    comments = requests.get("https://api.github.com/repos/ermaozi/get_subscribe/issues/1/comments")
    mail_re = re.compile("([a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+)")
    mail_list = []
    for i in comments.json():
        body = i.get("body")
        mail_list.extend(mail_re.findall(body))
    return mail_list


def send_mail(mail_list):
    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    receivers = mail_list

    with open("./mail/mail_template.html", "rb") as f:
        mail_msg = f.read().decode("utf-8")
    message = MIMEText(mail_msg, 'html', 'utf-8')

    message['From'] = formataddr(["二猫子的猛男助理", sender])
    message['Subject'] = f'{date_str} 订阅更新提醒'
    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, mail_port)
        smtpObj.login(mail_user, mail_pwd)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException as e:
        print("Error: 无法发送邮件", str(e))

def get_subscribe_url():
    dirs = './subscribe'
    if not os.path.exists(dirs):
        os.makedirs(dirs)
    log_dir = "./log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    rss = feedparser.parse('http://feeds.feedburner.com/mattkaydiary/pZjG')
    entries = rss.get("entries")
    if not entries:
        write_log("更新失败！无法拉取原网站内容", "ERROR")
        return
    update_list = []
    for i in entries:
        summary = i.get("summary")
        v2ray_list = re.findall(r"v2ray\(若无法更新请开启代理后再拉取\)：(.+?)</div>", summary)
        # 获取普通订阅链接
        if v2ray_list:
            v2ray_url = v2ray_list[-1].replace('amp;', '')
            v2ray_req = requests.request("GET", v2ray_url, verify=False)
            v2ray_code = v2ray_req.status_code
            if v2ray_code not in ok_code:
                write_log(f"获取 v2ray 订阅失败：{v2ray_url} - {v2ray_code}", "WARN")
            else:
                update_list.append(f"v2ray: {v2ray_code}")
                with open(dirs + '/v2ray.txt', 'w', encoding="utf-8") as f:
                    f.write(v2ray_req.text)
        clash_list = re.findall(r"clash\(若无法更新请开启代理后再拉取\)：(.+?)</div>", summary)
        # 获取clash订阅链接
        if clash_list:
            clash_url = clash_list[-1].replace('amp;', '')
            clash_req = requests.request("GET", clash_url, verify=False)
            clash_code = clash_req.status_code
            if clash_code not in ok_code:
                write_log(f"获取 clash 订阅失败：{clash_url} - {clash_code}", "WARN")
            else:
                update_list.append(f"clash: {clash_code}")
                with open(dirs + '/clash.yml', 'w', encoding="utf-8") as f:
                    clash_content = clash_req.content.decode("utf-8")
                    clash_content = clash_content.replace('https://www.mattkaydiary.com', "干死日本鬼子")
                    f.write(clash_content)
        if update_list:
            if mail_flag:
                send_mail(get_mail())
            write_log(f"更新成功：{update_list}", "INFO")
            return
    write_log(f"未能获取新的更新内容", "WARN")


def main():
    get_subscribe_url()


# 主函数入口
if __name__ == '__main__':
    mail_flag = False
    if len(sys.argv) == 6:
        mail_user = sys.argv[1]
        sender = sys.argv[2]
        mail_pwd = sys.argv[3]
        mail_host = sys.argv[4]
        mail_port = sys.argv[5]
        mail_flag = True
    main()