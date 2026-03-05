import streamlit as st
import pandas as pd
import mysql.connector
import os
import random
import json
from dotenv import load_dotenv
load_dotenv()
db_config = {
  'host': os.getenv('MYSQL_HOST'),
  'port': os.getenv('MYSQL_PORT'),
  'user': os.getenv('MYSQL_USER'),
  'password': os.getenv('MYSQL_ROOT_PASSWORD'),
  'database': os.getenv('MYSQL_DATABASE')
}
@st.cache_data
def load_data(query):
  conn = mysql.connector.connect(**db_config)
  cursor = conn.cursor()
  cursor.execute(query)
  data_list = cursor.fetchall()
  columns = [col[0] for col in cursor.description]
  cursor.close()
  conn.close()
  return pd.DataFrame(data_list, columns=columns)
def quote(filepath):
  with open(filepath, 'r', encoding='utf-8') as f:
    aa = json.load(f)
    qq = []
    for b in aa:
      qq.append(b)
  return random.choice(qq)
st.title("測試")
ind_df = load_data("select ind_name from industries where ind_name is not null;")
ind_list = ind_df['ind_name'].tolist()
selected_ind = st.sidebar.selectbox("請選擇天命", ind_list)
dy_sql = f"""
  select c.custNo, c.name as 公司名稱
  from company c
  join industries i 
  on c.ind_code = i.ind_code
  where i.ind_name = '{selected_ind}'
"""
st.write(f"目前選擇的產業: {selected_ind}")
# 名言佳句
my_quote = quote('words.json')
st.markdown(f"> *{my_quote}*")
f_sql = load_data(dy_sql)
st.dataframe(f_sql)