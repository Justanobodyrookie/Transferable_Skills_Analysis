import json
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

db_config = {
	'host': os.getenv('MYSQL_HOST'),
	'port': os.getenv('MYSQL_PORT'),
	'user': os.getenv('MYSQL_USER'),
	'password': os.getenv('MYSQL_PASSWORD'),
	'database': os.getenv('MYSQL_DATABASE')	
}
def parse_json():
	with open('category.txt', 'r', encoding='utf-8') as f:
		data = json.load(f)
	result = []
	for l1 in data:
		