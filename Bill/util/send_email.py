import smtplib
from email.mime.text import MIMEText


class EmailSender(object):

    def __init__(self):

        self.mail_host = "mail.purang.com"         # 服务器地址
        self.mail_user = "liubowen@purang.com"     # 邮箱
        self.mail_pass = "F2477o50"                # 密码/授权码
        self.sender = 'liubowen@purang.com'        # 发送人
        self.receivers = [
                            'liubowen@purang.com',
                            '15670356867@163.com',
                          ]                        # 接收人

    def send(self, title, content):

        message = MIMEText(content, 'plain', 'utf-8')  # 内容, 格式, 编码
        message['Subject'] = title
        message['From'] = "{}".format(self.sender)
        message['To'] = ",".join(self.receivers)

        try:
            smtp_obj = smtplib.SMTP_SSL(self.mail_host, 465)                     # 启用SSL发信, 端口一般是465
            smtp_obj.login(self.mail_user, self.mail_pass)                       # 登录验证
            smtp_obj.sendmail(self.sender, self.receivers, message.as_string())  # 发送
            print("mail has been send successfully.")
        except smtplib.SMTPException as e:
            print(e)


if __name__ == '__main__':
    EmailSender().send('爬虫名+时间+异常', '爬虫名+异常原因+时间+代码位置')

