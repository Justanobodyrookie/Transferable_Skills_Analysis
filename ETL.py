import re
import json
import os
import boto3
import traceback
import mysql.connector
from datetime import datetime
from job_crawler.job_crawler.gmail import send_error
from dotenv import load_dotenv
load_dotenv()

try:
	db_config = {
		'host': os.getenv('MYSQL_HOST'),
		'port': os.getenv('MYSQL_PORT'),
		'user': os.getenv('MYSQL_USER'),
		'password': os.getenv('MYSQL_ROOT_PASSWORD'),
		'database': os.getenv('MYSQL_DATABASE')
	}
	endpoint = os.getenv('MINIO_ENDPOINT')
	access_key = os.getenv('MINIO_USER')
	secret_key = os.getenv('MINIO_PASSWORD')
	bucket_name = 'job-data'
	prefix = ''
	s3 = boto3.client(
	    's3',
	    endpoint_url=endpoint,
	    aws_access_key_id=access_key,
	    aws_secret_access_key=secret_key,
	    region_name='us-east-1'
	    )
	company_list = []
	paginator = s3.get_paginator('list_objects_v2')
	pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
	count = 0
	conn = None
	cursor = None
	try:
		conn = mysql.connector.connect(**db_config)
		cursor = conn.cursor()
		jobs_list = []
		# company
		sql_insert_company = """insert ignore into company (custNo, ind_code, name) values (%s, %s, %s)"""
		sql_get_company_id = """select custNo, id from company"""
		# jobs
		s10_map = {10: 1, 20: 2, 30: 3, 40: 4, 50: 5, 60: 6}
		raw_job_list = []
		sql_insert_jobs = """insert ignore into jobs (company_id, region_code, edu_id, job_code, job_title, location, response_pr, apply_num, salary_type, salary_min, salary_max, remote, job_released, no_exper, link, snapshot_date) 
			values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		"""
		# job_skills
		with open('skills.txt', 'r', encoding='utf-8') as f:
			sk = json.load(f)
		sql_get_skills = """select lower(name), id from skills"""
		sql_get_jobskills = """select job_code, id from jobs"""
		sql_insert_jobs_skills = """insert ignore into job_skills (job_id, skills_id) values (%s, %s)"""
		cursor.execute(sql_get_skills)
		skill_dict = {row[0]: row[1] for row in cursor.fetchall()}
		raw_job_skills_list = []
		# industries
		sql_insert_industries = """insert ignore into industries (ind_code, ind_name) values (%s, %s)"""
		ind_list = []
		# job_category_relations
		raw_job_cate = []
		sql_insert_job_category_relations = """insert ignore into job_category_relations (job_id, category_code) values (%s, %s)"""
		# job_benefits
		sql_insert_job_benefits = """insert ignore into job_benefits (job_id, be_code) values (%s, %s)"""
		raw_job_benefits = []
		# job_languages
		sql_insert_job_languages = """insert ignore into job_languages (job_id, language_id, speak, listen, reading, writing) values (%s, %s, %s, %s, %s, %s)"""
		raw_job_languages = []
		for page in pages:
			if 'Contents' in page:
				for obj in page['Contents']:
					s = obj['Key']
					current_job_skills = []
					file = s3.get_object(Bucket=bucket_name, Key=s)
					fi = file['Body'].read().decode('utf-8')
					js_fi = json.loads(fi)
					aa = js_fi['raw_data']
					current_des = aa['description']
					current_tools = []
					if 'pcSkills' in aa:
						for g in aa['pcSkills']:
							h = g['description']
							current_tools.append(h)
					if isinstance(current_tools, list):
						current_tools = ','.join(current_tools)
					else:
						current_tools = str(current_tools)
					if isinstance(current_des, list):
						current_des = ','.join(current_des)
					else:
						current_des = str(current_des)
					eng_wd = re.findall(r'[A-Za-z][A-Za-z0-9+#]*', current_tools)
					eng_wt = re.findall(r'[A-Za-z][A-Za-z0-9+#]*', current_des)
					s10 = js_fi['raw_data']['s10']
					job_des = [w.lower() for w in eng_wd]
					job_tools = [a.lower() for a in eng_wt]
					raw = js_fi['raw_data']
					jan = raw.get('jobAddrNoDesc') or ''
					ja = raw.get('jobAddress') or ''
					# jobs
					region = js_fi['region_code']
					edu = js_fi['raw_data']['optionEdu'][0]
					job_edu = js_fi['raw_data']['optionEdu']
					job_code = js_fi['job_code']
					job_title = js_fi['raw_data']['jobName']
					location = jan + ja
					response_pr = js_fi['raw_data']['hrBehaviorPR']
					apply_num = js_fi['raw_data']['applyCnt']
					salary_type = s10_map.get(s10, 0)
					if s10 == 10:
						salary_min = 40000
						salary_max = 40000
					else:
						salary_min = js_fi['raw_data']['salaryLow']
						salary_max = js_fi['raw_data']['salaryHigh']
					remote = js_fi['raw_data']['remoteWorkType']
					job_released = js_fi['raw_data']['appearDate']
					if '無經驗可' in job_des or '無經驗可' in job_title:
						no_exper = 1
					else:
						no_exper = 0
					job_link = js_fi['raw_data']['link']['job']
					snapshot_date = s.split('/')[0]
					# -----
					# company
					company_no = js_fi['raw_data']['custNo']
					company_name = js_fi['raw_data']['custName']
					# industries
					ind_code = js_fi['raw_data']['coIndustry']
					ind_name = js_fi['raw_data']['coIndustryDesc']
					ind_list.append((ind_code, ind_name))
					tjt = (
	    				company_no, region, edu, job_code, job_title, location, 
	    				response_pr, apply_num, salary_type, salary_min, salary_max, 
	    				remote, job_released, no_exper, job_link, snapshot_date
						)
					raw_job_list.append(tjt)
					company_list.append((company_no, ind_code, company_name))
					combined_text = current_des + ' ' + current_tools
					combined_lower = combined_text.lower()
					for sk1 in sk:
						a = sk1['des']
						if 'n' in sk1:
							for sk2 in sk1['n']:
								b = sk2['des']
								if 'n' in sk2:
									for sk3 in sk2['n']:
										if isinstance(sk3, str):
											if '+' in sk3 or '#' in sk3:
												safe_lang = re.escape(sk3)
												pattern = r'\b' + safe_lang + r'(?!\w)'
											else:
												pattern = r'\b' + sk3 + r'\b'
											match = re.findall(pattern, combined_text, re.IGNORECASE)
											if match:
												if sk3.lower() not in current_job_skills:
													current_job_skills.append(sk3.lower())
										else:
											c = sk3.get('skill_name', '')
											d = sk3.get('require_all', [])
											e = sk3.get('require_any', [])
											if all(word.lower() in combined_lower for word in d):
												match_e = [word for word in e if word.lower() in combined_lower]
												for word in match_e:
													if d and match_e:
														plus = d[0] + word
														if plus.lower() not in current_job_skills:
															current_job_skills.append(plus.lower())
													elif match_e:
														plus = match_e[0]
														if plus.lower() not in current_job_skills:
															current_job_skills.append(plus.lower())
					raw_job_skills_list.append((job_code, current_job_skills))
					# job_category
					for jc in js_fi['raw_data']['jobCat']:
						raw_job_cate.append((job_code, jc))
					# job_benefits
					for jb in js_fi['raw_data']['tags']:
						raw_job_benefits.append((job_code, jb))
					# job_languages
					job_lang = js_fi['raw_data'].get('languageRequirements') or []
					for jl in job_lang:
						jl_id = jl.get('language')
						ab = jl.get('ability', {})
						jl_speak = ab.get('speaking')
						jl_listen = ab.get('listening')
						jl_read = ab.get('reading')
						jl_write = ab.get('writing')
						raw_job_languages.append((job_code, jl_id, jl_speak, jl_listen, jl_read, jl_write))
					count = count + 1
					if count % 1000 == 0:
						cursor.executemany(sql_insert_industries, ind_list)
						cursor.executemany(sql_insert_company, company_list)
						# company
						cursor.execute(sql_get_company_id)
						all_company = cursor.fetchall()
						company_dict = {row[0]: row[1] for row in all_company}
						jl = []
						for rj in raw_job_list:
							com_no = rj[0]
							real_id = company_dict.get(com_no)
							if real_id:
								fi = (real_id,) + rj[1:]
								jl.append(fi)
						cursor.executemany(sql_insert_jobs, jl)
						# skills
						cursor.execute(sql_get_jobskills)
						job_dict = {row[0]: row[1] for row in cursor.fetchall()}
						js_list = []
						for rjs in raw_job_skills_list:
							jc = rjs[0]
							skill_names = rjs[1]
							real_job_id = job_dict.get(jc)
							if real_job_id:
								for s_name in skill_names:
									real_skill_id = skill_dict.get(s_name)
									if real_skill_id:
										js_list.append((real_job_id, real_skill_id))
						jcr_list = []
						for rjc in raw_job_cate:
							jc_code = rjc[0]
							cat_val = rjc[1]
							real_job_id = job_dict.get(jc_code)
							if real_job_id:
								jcr_list.append((real_job_id, cat_val))
						jb_list = []
						for rjb in raw_job_benefits:
							jb_code = rjb[0]
							be_code = rjb[1]
							real_job_id = job_dict.get(jb_code)
							if real_job_id:
								jb_list.append((real_job_id, be_code))
						jl_list = []
						for rjl in raw_job_languages:
							jl_code = rjl[0]
							rjl_id = rjl[1]
							speak_l = rjl[2]
							listen_l = rjl[3]
							read_l = rjl[4]
							write_l = rjl[5]
							real_job_id = job_dict.get(jl_code)
							if real_job_id:
								jl_list.append((real_job_id, rjl_id, speak_l, listen_l, read_l, write_l))
						cursor.executemany(sql_insert_jobs_skills, js_list)
						cursor.executemany(sql_insert_job_category_relations, jcr_list)
						cursor.executemany(sql_insert_job_benefits, jb_list)
						cursor.executemany(sql_insert_job_languages, jl_list)
						conn.commit()
						company_list.clear()
						raw_job_list.clear()
						js_list.clear()
						raw_job_skills_list.clear()
						raw_job_cate.clear()
						ind_list.clear()
						jcr_list.clear()
						raw_job_benefits.clear()
						jb_list.clear()
						raw_job_languages.clear()
						jl_list.clear()
						print(f"已處理 {count} 筆資料")
		if len(raw_job_list) > 0:
			cursor.executemany(sql_insert_industries, ind_list)
			cursor.executemany(sql_insert_company, company_list)
			# company
			cursor.execute(sql_get_company_id)
			all_company = cursor.fetchall()
			company_dict = {row[0]: row[1] for row in all_company}
			jl = []
			for rj in raw_job_list:
				com_no = rj[0]
				real_id = company_dict.get(com_no)
				if real_id:
					fi = (real_id,) + rj[1:]
					jl.append(fi)
			cursor.executemany(sql_insert_jobs, jl)
			# skills
			cursor.execute(sql_get_jobskills)
			job_dict = {row[0]: row[1] for row in cursor.fetchall()}
			js_list = []
			for rjs in raw_job_skills_list:
				jc = rjs[0]
				skill_names = rjs[1]
				real_job_id = job_dict.get(jc)
				if real_job_id:
					for s_name in skill_names:
						real_skill_id = skill_dict.get(s_name)
						if real_skill_id:
							js_list.append((real_job_id, real_skill_id))
			jcr_list = []
			for rjc in raw_job_cate:
				jc_code = rjc[0]
				cat_val = rjc[1]
				real_job_id = job_dict.get(jc_code)
				if real_job_id:
					jcr_list.append((real_job_id, cat_val))
			jb_list = []
			for rjb in raw_job_benefits:
				jb_code = rjb[0]
				be_code = rjb[1]
				real_job_id = job_dict.get(jb_code)
				if real_job_id:
					jb_list.append((real_job_id, be_code))
			jl_list = []
			for rjl in raw_job_languages:
				jl_code = rjl[0]
				rjl_id = rjl[1]
				speak_l = rjl[2]
				listen_l = rjl[3]
				read_l = rjl[4]
				write_l = rjl[5]
				real_job_id = job_dict.get(jl_code)
				if real_job_id:
					jl_list.append((real_job_id, rjl_id, speak_l, listen_l, read_l, write_l))
			cursor.executemany(sql_insert_jobs_skills, js_list)
			cursor.executemany(sql_insert_job_category_relations, jcr_list)
			cursor.executemany(sql_insert_job_benefits, jb_list)
			cursor.executemany(sql_insert_job_languages, jl_list)
			conn.commit()
			company_list.clear()
			raw_job_list.clear()
			js_list.clear()
			raw_job_skills_list.clear()
			raw_job_cate.clear()
			ind_list.clear()
			jcr_list.clear()
			raw_job_benefits.clear()
			jb_list.clear()
			raw_job_languages.clear()
			jl_list.clear()
			print(f"尾數寫入完成")
	except Exception as e:
		print(f"匯入時發生錯誤: {e}")
		traceback.print_exc()
		send_error(str(e), subject=f"ETL寫入資料庫失敗: {e}")
	finally:
		if conn and conn.is_connected():
			if cursor:
				cursor.close()
			conn.close()
			print(f"成功關閉conn & cursor")
except Exception as e:
	send_error(str(e), subject=f"ETL啟動失敗: {e}")
	print(f"出問題囉 弟弟: {e}")