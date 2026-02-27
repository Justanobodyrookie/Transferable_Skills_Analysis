import json
import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

db_config = {
	'host': 'localhost',
	'port': '3308',
	'user': os.getenv('MYSQL_USER'),
	'password': os.getenv('MYSQL_ROOT_PASSWORD'),
	'database': os.getenv('MYSQL_DATABASE')
}

def parse_json():
	with open('edu.txt', 'r', encoding='utf-8') as f:
		data = json.load(f)
	result = []
	for k, v in data.items():
		re = (k, v)
		result.append(re)
	return result
def save_db(data_list):
	conn = None
	cursor = None
	try:
		conn = mysql.connector.connect(**db_config)
		cursor = conn.cursor()
		sql = """
			insert ignore into education
			(edu_code, name)
			values (%s, %s)
		"""
		cursor.executemany(sql, data_list)
		conn.commit()
		print(f"成功匯入 {cursor.rowcount} 筆資料")
	except Exception as e:
		print(f"匯入時發生錯誤: {e}")
	finally:
		if conn and conn.is_connected():
			cursor.close()
			conn.close()
			print(f"成功關閉cursor & conn")
if __name__ == '__main__':
	a = parse_json()
	save_db(a)
	print(f"解析完成, 共 {len(a)} 筆資料")	