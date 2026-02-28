import json
import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

db_config = {
	'host': os.getenv('MYSQL_HOST'),
	'port': os.getenv('MYSQL_PORT'),
	'user': os.getenv('MYSQL_USER'),
	'password': os.getenv('MYSQL_ROOT_PASSWORD'),
	'database': os.getenv('MYSQL_DATABASE')
}

def parse_json():
	with open('skills.txt', 'r', encoding='utf-8') as f:
		data = json.load(f)
	result = []
	for l1 in data:
		# (code, parent_code, name, level)
		l1_tuple = (l1['no'], None, l1['des'], 1)
		result.append(l1_tuple)
		if 'n' in l1:
			for l2 in l1['n']:
				l2_tuple = (l2['no'], l1['no'], l2['des'], 2)
				result.append(l2_tuple)
				if 'n' in l2:
					for l3 in l2['n']:
						if isinstance(l3, str):
							l3_tuple = (None, l2['no'], l3, 3)
						else:
							l3_tuple = (None, l2['no'], l3['skill_name'], 3)
						result.append(l3_tuple)

	return result

def save_db(datalist):
	conn = None
	try:
		conn = mysql.connector.connect(**db_config)
		cursor = conn.cursor()
		sql = """
			insert ignore into skills
			(id, parent_id, name, level)
			values (%s, %s, %s, %s)
		"""
		cursor.executemany(sql, datalist)
		conn.commit()
		print(f"資料共 {cursor.rowcount} 筆資料")
	except Exception as e:
		print(f"匯入失敗: {e}")
	finally:
		if conn and conn.is_connected():
			cursor.close()
			conn.close()
			print(f"成功關閉連線")
if __name__ == '__main__':
	a = parse_json()
	save_db(a)
	print(f"解析完畢,共 {len(a)} 筆資料")