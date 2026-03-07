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
def db_search(query, params=None):
    conn = mysql.connector.connect(**db_config)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    options = ["請選擇"] + df.iloc[:, 0].tolist()
    return options
# SQL區
ind_df = load_data("select ind_name from industries where ind_name is not null;")
ind_list = ind_df['ind_name'].tolist()
last_sql = f"""
    group by s3.name, s2.name, s.name
    )
    select 排名, 大類, 中類, 技能名稱
    from rank_spell
    where 排名 <= 10
    order by 中類, 排名;
"""
base_sql = f"""
    with rank_spell as (
        select
            row_number() over(partition by s2.name order by count (disinct j.job_code) desc) as 排名,
            s3.name as 大類,
            s2.name as 中類,
            s.name as 技能名稱,
            count(disinct j.job_code) as 出現次數
        from jobs j
        join job_skills js on j.id = js.job_id
        join skills s on js.skills_id = s.id
        join skills s2 on s.parent_id = s2.id
        join skills s3 on s2.parent_id = s3.id
        join job_category_relations jcr on j.id = jcr.job_id
        join job_category jc on jc.code = jcr.category_code
        join company c on j.company_id = c.id
        join industries i on c.ind_code = i.ind_code
        where 1 = 1
"""

# 標題
st.title("職務技能需求表")
# 名言佳句
my_quote = quote('words.json')
st.markdown(f"> *{my_quote}*")

# 按鈕部門
glue = []

col1, col2, col3, col4, col5 = st.columns(5)
big_cate = "請選擇"
middle_cate = "請選擇"
small_cate = "請選擇"
industry = "請選擇"
with col1:
    sql_big = "select name from job_category where level = 1"
    big_opt = db_search(sql_big)
    big_cate = st.selectbox("職務類別", big_opt)
if big_cate != "請選擇":
  with col2:
    sql_middle = "select name from job_category where level = 2"
    middle_opt = db_search(sql_middle)
    middle_cate = st.selectbox("職務中項", middle_opt)
    if middle_cate != "請選擇":
        with col3:
            sql_small = "select name from job_category where level = 3"
            small_opt = db_search(sql_small)
            small_cate = st.selectbox("職務細項", small_opt)
with col4:
    sql_industry = "select ind_name from industries"
    industry_opt = db_search(sql_industry)
    industry = st.selectbox("產業分類", industry_opt)
with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    search_button = st.button("搜尋")
if search_button:
    st.write("---")
    st.write(f"目前搜尋條件: 大類:{big_cate} / 中類:{middle_cate} / 小類:{small_cate}")
    if middle_cate != "請選擇":
        base_sql = base_sql + " and jc.name = %s"
        glue.append(middle_cate)
    if small_cate != "請選擇":
        base_sql = base_sql + " and jc.name = %s"
        glue.append(small_cate)
    if industry != "請選擇":
        base_sql = base_sql + " and jc.name = %s"
        glue.append(industry)
    base_sql = base_sql + last_sql   
    f_sql = load_data(base_sql, glue)
    st.dataframe(f_sql)