import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
load_dotenv()

def send_error(error_message, subject):
	sender = os.getenv('GMAIL_USER')
	password = os.getenv('GMAIL_PASS')
	receiver = os.getenv('GMAIL_USER')
	msg = MIMEText(f"出事啦, 趕快來修: \n\n{error_message}")
	msg['Subject'] = subject
	msg['From'] = sender
	msg['To'] = receiver
	try:
		server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
		server.login(sender, password)
		server.send_message(msg)
		server.quit()
	except Exception as e:
		print(f"郵件發送失敗: {e}")