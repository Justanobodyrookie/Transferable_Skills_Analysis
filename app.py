import streamlit as st
import pandas as pd
import mysql.connector
import os
import random
import json
import plotly.express as px
from dotenv import load_dotenv
load_dotenv()
db_config = {
  'host': os.getenv('MYSQL_HOST'),
  'port': os.getenv('MYSQL_PORT'),
  'user': os.getenv('MYSQL_USER'),
  'password': os.getenv('MYSQL_ROOT_PASSWORD'),
  'database': os.getenv('MYSQL_DATABASE')
}
@st.cache_data(ttl=3600)
def load_data(query, params=None):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query, params)
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
@st.cache_data(ttl=3600)
def db_search(query, params=None):
    conn = mysql.connector.connect(**db_config)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    options = ["請選擇"] + df.iloc[:, 0].tolist()
    return options

page = st.sidebar.radio("系統功能", ['職務技能需求表', '技能適配度檢測'])
# SQL區
ind_df = load_data("select ind_name from industries where ind_name is not null;")
ind_list = ind_df['ind_name'].tolist()
last_sql = f"""
    group by s3.name, s2.name, s.name
    )
    select 排名, 大類, 中類, 技能名稱, 出現次數
    from rank_spell
    where 排名 <= 10
    order by 中類, 排名;
"""
base_sql = f"""
    with rank_spell as (
        select
            row_number() over(partition by s2.name order by count(distinct j.job_code) desc) as 排名,
            s3.name as 大類,
            s2.name as 中類,
            s.name as 技能名稱,
            count(distinct j.job_code) as 出現次數
        from jobs j
        join job_skills js on j.id = js.job_id
        join skills s on js.skills_id = s.id
        join skills s2 on s.parent_id = s2.id
        join skills s3 on s2.parent_id = s3.id
        join job_category_relations jcr on j.id = jcr.job_id
        join job_category jc on jc.code = jcr.category_code
        join company c on j.company_id = c.id
        join industries i on c.ind_code = i.ind_code
        join job_category jc_small on jc_small.code = jcr.category_code
        left join job_category jc_mid on jc_small.parent_code = jc_mid.code
        left join job_category jc_big on jc_mid.parent_code = jc_big.code
        where 1 = 1
"""

if page == '職務技能需求表':
    # 標題
    st.title("職務技能需求表")
    st.markdown("""
        <style>
        /* 隱藏 dataframe 右上角整組工具列 */
        [data-testid="stElementToolbar"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    # 名言佳句
    my_quote = quote('words.json')
    st.markdown(f"> *{my_quote}*")

    # 按鈕部門
    glue = []

    col1, col2, col3, col4, col5 = st.columns([24, 24, 24, 24, 12])
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
        sql_middle = """select j1.name from job_category j1 join job_category j2 on j1.parent_code = j2.code where j2.name = %s"""
        middle_opt = db_search(sql_middle, params=(big_cate,))
        middle_cate = st.selectbox("職務中項", middle_opt)
        if middle_cate != "請選擇":
            with col3:
                sql_small = """select j1.name from job_category j1 join job_category j2 on j1.parent_code = j2.code where j2.name = %s"""
                small_opt = db_search(sql_small, params=(middle_cate,))
                small_cate = st.multiselect("職務細項", small_opt)
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
        if small_cate:
            protect = ', '.join(['%s'] * len(small_cate))
            base_sql = base_sql + f" and jc_small.name in ({protect})"
            glue.extend(small_cate)
            # base_sql = base_sql + " and jc_small.name = %s"
            # glue.append(small_cate)
        elif middle_cate != "請選擇":
            base_sql = base_sql + " and jc_mid.name = %s"
            glue.append(middle_cate)
        elif big_cate != "請選擇":
            base_sql = base_sql + " and jc_big.name = %s"
            glue.append(big_cate)
        if industry != "請選擇":
            base_sql = base_sql + " and i.ind_name = %s"
            glue.append(industry)
        base_sql = base_sql + last_sql   
        f_sql = load_data(base_sql, tuple(glue))
        f_sql['出現次數'] = pd.to_numeric(f_sql['出現次數'], errors='coerce')
        f_sql['佔比'] = (f_sql['出現次數'] / f_sql.groupby('中類')['出現次數'].transform('sum') * 100).round(1).astype(str) + '%'
        skill_count = f_sql[['大類', '中類', '技能名稱']].notnull().sum(axis=1)
        clean_stuff = (skill_count >= 3) & (f_sql['出現次數'] > 5)
        f_sql = f_sql[clean_stuff]
        st.dataframe(f_sql, hide_index=True,column_order=("排名", "大類", "中類", "技能名稱", "佔比"))

elif page == '技能適配度檢測':
    st.title('技能適配度檢測')
    st.markdown("""
        <style>
        /* 隱藏 dataframe 右上角整組工具列 */
        [data-testid="stElementToolbar"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    my_quote = quote('words.json')
    st.markdown(f"> *{my_quote}*")
    # 按鈕部門
    glue = []
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        sql_mid_option = "select name from skills where level = 2"
        mid_opt = db_search(sql_mid_option)
        select_mid = st.multiselect("技能中類", mid_opt)
    with col2:
        if select_mid:
            delete_choice = [m for m in select_mid if m != '請選擇']
            if delete_choice:
                defense_mid = ', '.join(['%s'] * len(delete_choice))
                sql_samll_option = f"select s1.name from skills s1 join skills s2 on s1.parent_id = s2.id where s2.name in ({defense_mid})"
                small_df = load_data(sql_samll_option, tuple(delete_choice))
                small_opt = small_df.iloc[:, 0].tolist()
                select_small = st.multiselect("技能細項", small_opt)
            else:
                select_small = st.multiselect("技能細項", [])
        else:
            select_small = st.multiselect("技能細項", [])
    with col3:
        select_langs = st.multiselect('語言', ['英文', '日文'])
        user_lang_levels = {}
    with col4:
        if select_langs:
            for lang in select_langs:
                level = st.selectbox(f"{lang} 程度", ['不拘', '略懂', '中等', '精通'], key=f"level_{lang}")
                user_lang_levels[lang] = level
        else:
            st.markdown("<span style='color:gray; font-size:14px;'>請先選擇語言</span>", unsafe_allow_html=True)
    with col5:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("開始分析")
    if analyze_button:
        if not select_small or not select_langs:
            st.warning("請至少選擇一項技能與語言")
            st.stop()
        st.write('---')
        st.write(f"您的技能包: {select_small}")
        st.write(f"您的語言能力: {select_langs} ({user_lang_levels})")
        level_accept_map = {
            "不拘": [0],
            "略懂": [0, 4],
            "中等": [0, 4, 8],
            "精通": [0, 4, 8, 2]
        }
        lang_conditions = []
        lang_params = []
        final_params = []
        defense = ', '.join(['%s'] * len(select_small))
        final_params.extend(select_small)
        for lang, level_text in user_lang_levels.items():
            acc_code = level_accept_map[level_text]
            defense_lang = ', '.join(['%s'] * len(acc_code))
            step1 = f"""(
                l.name = %s 
                and jl.speak in ({defense_lang})
                and jl.listen in ({defense_lang})
                and jl.reading in ({defense_lang})
                and jl.writing in ({defense_lang})
            )"""
            lang_conditions.append(step1)
            lang_params.append(lang)
            lang_params.extend(acc_code)
            lang_params.extend(acc_code)
            lang_params.extend(acc_code)
            lang_params.extend(acc_code)
        final_lang_sql = " or ".join(lang_conditions)
        final_params.extend(lang_params)
        final_sql = f"""
            with match_jobs as (
                select j.id, j.no_exper
                from jobs j
                join job_skills js on j.id = js.job_id
                join skills s on js.skills_id = s.id
                where s.name in ({defense})
                group by j.id, j.no_exper
                having count(distinct s.name) = {len(select_small)}
                ),
            match_langs as (
                select jl.job_id
                from job_languages jl
                join languages l on jl.language_id = l.id
                where {final_lang_sql}
                group by jl.job_id
                having count(l.name) = {len(select_langs)}
            )
                select
                    count(mj.id) as 總職缺數,
                    sum(mj.no_exper) as 無經驗可
                from match_jobs mj
                join match_langs ml on mj.id = ml.job_id;
        """
        result_df = load_data(final_sql, tuple(final_params))
        total_jobs = int(result_df['總職缺數'].iloc[0])
        raw_no_exp = result_df['無經驗可'].iloc[0]
        no_exp_jobs = 0 if pd.isna(raw_no_exp) else int(raw_no_exp)
        if total_jobs > 0:
            no_exp_ratio = round((no_exp_jobs / total_jobs) * 100, 1)
        else:
            no_exp_ratio = 0
        st.write('### 職缺市場機會')
        # 薪水地帶
        salary_sql = f"""
            with match_jobs as (
                select j.id, j.no_exper
                from jobs j
                join job_skills js on j.id = js.job_id
                join skills s on js.skills_id = s.id
                where s.name in ({defense})
                group by j.id, j.no_exper
                having count(distinct s.name) = {len(select_small)}
                ),
            match_langs as (
                select jl.job_id
                from job_languages jl
                join languages l on jl.language_id = l.id
                where {final_lang_sql}
                group by jl.job_id
                having count(l.name) = {len(select_langs)}
            )
            select
                j.salary_type,
                count(j.id) as 職缺數,
                round(avg(case when j.salary_min > 0 then j.salary_min else null end), 0) as 平均底薪,
                round(avg(case when j.salary_max > 0 then j.salary_max else null end), 0) as 平均天花板
            from match_jobs mj
            join match_langs ml on mj.id = ml.job_id
            join jobs j on mj.id = j.id
            group by j.salary_type;
        """
        m1, m2 = st.columns(2)
        salary_df = load_data(salary_sql, tuple(final_params))
        with m1:
            st.metric(label="符合技能的職缺總數", value=f"{total_jobs} 筆")
        with m2:
            st.metric(label="無經驗可接受比例", value=f"{no_exp_ratio} %")
        if not salary_df.empty:
            type_map = {1: '面議', 2: '論件', 3: '時薪', 4: '日薪', 5: '月薪', 6: '年薪'}
            salary_df['薪資類型'] = salary_df['salary_type'].map(type_map)
            st.write('---')
            st.write('### 薪資分析')
            circle_col, data_col = st.columns([6, 4])
            with circle_col:
                fig = px.pie(salary_df, values='職缺數', names='薪資類型', title='薪資方式佔比')
                st.plotly_chart(fig, use_container_width=True)
            with data_col:
                month_data = salary_df[salary_df['salary_type'] == 5]
                if not month_data.empty:
                    m_min = int(month_data['平均底薪'].iloc[0])
                    m_max = int(month_data['平均天花板'].iloc[0])
                    st.metric(label='月薪範圍', value=f"{m_min} ~ {m_max}")
                year_data = salary_df[salary_df['salary_type'] == 6]
                if not year_data.empty:
                    m_min = int(year_data['平均底薪'].iloc[0])
                    st.metric(label='年薪上看', value=f"{m_min}")
                negoative_data = salary_df[salary_df['salary_type'] == 1]
                if not negoative_data.empty:
                    st.metric(label='面議', value=f"取決於談判技巧")
                piecework_data = salary_df[salary_df['salary_type'] == 2]
                if not piecework_data.empty:
                    m_min = int(piecework_data['平均底薪'].iloc[0])
                    m_max = int(piecework_data['平均天花板'].iloc[0])
                    st.metric(label='論件計酬', value=f"{m_min} ~ {m_max}")
                part_time_data = salary_df[salary_df['salary_type'] == 3]
                if not part_time_data.empty:
                    m_min = int(part_time_data['平均底薪'].iloc[0])
                    st.metric(label='時薪平均', value=f"{m_min}")
        st.write('---')
        st.write('### 適合的職務方向')
        rank_sql = f"""
            with match_jobs as (
                select j.id, j.no_exper
                from jobs j
                join job_skills js on j.id = js.job_id
                join skills s on js.skills_id = s.id
                where s.name in ({defense})
                group by j.id, j.no_exper
                having count(distinct s.name) = {len(select_small)}
                ),
            match_langs as (
                select jl.job_id
                from job_languages jl
                join languages l on jl.language_id = l.id
                where {final_lang_sql}
                group by jl.job_id
                having count(l.name) = {len(select_langs)}
            )
            select
                jc.name as 適合職缺細項,
                count(mj.id) as 匹配數量
            from match_jobs mj
            join match_langs ml on mj.id = ml.job_id
            join job_category jc on jcr.category_code = jc.code
            group by jc.name
            order by 匹配數量 desc
            limit 10;
        """