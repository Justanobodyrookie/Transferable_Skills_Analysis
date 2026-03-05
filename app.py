import streamlit as st
import pandas as pd
import mysql.connector
import os
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
  return pd.DataFrame(data, columns=columns)
st.title("測試")
test_sql = "SELECT * FROM industries LIMIT 10;"
df = load_data(test_sql)
st.dataframe(df)