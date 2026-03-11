import streamlit as st
import pandas as pd
import mysql.connector
import os
import random
import json
import bcrypt
from job_crawler.job_crawler.gmail import send_error
import plotly.express as px
from dotenv import load_dotenv
try:
    load_dotenv()
    st.set_page_config(layout="wide", page_title="轉職嗎?")
    db_config = {
      'host': os.getenv('MYSQL_HOST'),
      'port': os.getenv('MYSQL_PORT'),
      'user': os.getenv('MYSQL_USER'),
      'password': os.getenv('MYSQL_ROOT_PASSWORD'),
      'database': os.getenv('MYSQL_DATABASE')
    }
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    def verify_password(password, hash_password):
        return bcrypt.checkpw(password.encode('utf-8'), hash_password.encode('utf-8'))
    @st.cache_data(ttl=3600, max_entries=100)
    def load_data(query, params=None):
        conn = mysql.connector.connect(**db_config, pool_name="streamlit_pool", pool_size=3)
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
        return random.choice(aa)
    @st.cache_data(ttl=3600, max_entries=100)
    def db_search(query, params=None):
        conn = mysql.connector.connect(**db_config, pool_name="streamlit_pool", pool_size=3)
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        options = ["請選擇"] + df.iloc[:, 0].tolist()
        return options
    def execute_query(query, params=None):
        conn = mysql.connector.connect(**db_config, pool_name="streamlit_pool", pool_size=3)
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            send_error(str(err), subject=f"streamlit資料庫連線失敗: {err}")
            return False
        finally:
            cursor.close()
            conn.close()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if st.session_state['logged_in']:
        menu_options = ['職務技能需求表', '技能適配度檢測', '職缺閱覽']
    else:
        menu_options = ['職務技能需求表', '技能適配度檢測', '系統登入']
    if st.session_state['logged_in']:
        st.sidebar.markdown('---')
        st.sidebar.write(f"管理員: **{st.session_state['username']}**")
        if st.sidebar.button('登出'):
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.rerun()
    page = st.sidebar.radio("系統功能", menu_options)
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Contact:** hsu00093@gmail.com") # 換成你的真實信箱
    st.sidebar.markdown(
        "<span style='font-size: 0.8em; color: gray;'>本系統僅供個人興趣專案，爬取之資料不做任何商業用途。</span>", 
        unsafe_allow_html=True
    )
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
        q_col1, q_col2 = st.columns([1, 4])
        with q_col1:
            st.image(my_quote['image'], use_container_width=True)
        with q_col2:
            st.markdown(
                f"<h3 style='font-style: italic; color: lightgray; border-left: 5px solid gray; padding-left: 15px;'>“{my_quote['text']}”</h3>",
                unsafe_allow_html=True
            )
        st.write('---')

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
            if big_cate == "請選擇" and industry == "請選擇":
                st.warning("為避免資料量過大導致系統崩潰，請選擇一個職務類別及職務中項")
                st.stop()
            if big_cate != "請選擇" and middle_cate == "請選擇":
                st.warning("為避免資料量過大，請再選擇一個職務中項")
                st.stop()
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
        q_col1, q_col2 = st.columns([1, 4])
        with q_col1:
            st.image(my_quote['image'], use_container_width=True)
        with q_col2:
            st.markdown(
                f"<h3 style='font-style: italic; color: lightgray; border-left: 5px solid gray; padding-left: 15px;'>“{my_quote['text']}”</h3>",
                unsafe_allow_html=True
            )
        st.write('---')
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
            sql_lang = "select name from languages"
            land_df = load_data(sql_lang)
            lang_list = land_df['name'].tolist()
            select_langs = st.multiselect('語言', lang_list)
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
            if not select_small and not select_langs:
                st.warning("請至少選擇一項技能與語言")
                st.stop()
            st.write('---')
            st.write(f"您的技能包: {select_small}")
            st.write(f"您的語言能力: {select_langs} ({user_lang_levels})")
            dynamic_joins = []
            final_params = []
            if select_small:
                defense = ', '.join(['%s'] * len(select_small))
                skill_join = f"""
                    join(
                        select js.job_id
                        from job_skills js
                        join skills s on js.skills_id = s.id
                        where s.name in ({defense})
                        group by js.job_id
                        having count(distinct s.name) >= 1
                    ) as mj on j.id = mj.job_id
                """
                dynamic_joins.append(skill_join)
                final_params.extend(select_small)
            if select_langs:
                level_accept_map = {"不拘": [0], "略懂": [0, 4], "中等": [0, 4, 8], "精通": [0, 4, 8, 2]}
                lang_conditions = []
                for lang, level_text in user_lang_levels.items():
                    acc_code = level_accept_map[level_text]
                    defense_lang = ', '.join(['%s'] * len(acc_code))
                    step1 = f"""(
                        l.name = %s
                        and jl.speak in ({defense_lang})
                        and jl.listen in ({defense_lang})
                        and jl.writing in ({defense_lang})
                        and jl.reading in ({defense_lang})
                    )"""
                    lang_conditions.append(step1)
                    final_params.append(lang)
                    final_params.extend(acc_code * 4)
                final_lang_sql = " or ".join(lang_conditions)
                lang_join = f"""
                    join(
                        select jl.job_id
                        from job_languages jl
                        join languages l on jl.language_id = l.id
                        where {final_lang_sql}
                        group by jl.job_id
                        having count(l.name) >= 1
                    ) as ml on j.id = ml.job_id
                """
                dynamic_joins.append(lang_join)
            join_string = "\n".join(dynamic_joins)
            final_sql = f"""
                select
                    count(j.id) as 總職缺數,
                    sum(j.no_exper) as 無經驗可
                from jobs j
                {join_string};
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
                select
                    j.salary_type,
                    count(j.id) as 職缺數,
                    round(avg(case when j.salary_min > 0 then j.salary_min else null end), 0) as 平均底薪,
                    round(avg(case when j.salary_max > 0 then j.salary_max else null end), 0) as 平均天花板
                from jobs j
                {join_string}
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
                        st.metric(label='平均月薪', value=f"{m_min}")
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
                        st.metric(label='論件計酬', value=f"{m_min}")
                    part_time_data = salary_df[salary_df['salary_type'] == 3]
                    if not part_time_data.empty:
                        m_min = int(part_time_data['平均底薪'].iloc[0])
                        st.metric(label='時薪平均', value=f"{m_min}")
                st.write('---')
                st.write('### 適合的職務方向')
                rank_sql = f"""
                    select
                        jc.name as 適合職缺,
                        count(j.id) as 匹配數量
                    from jobs j
                    {join_string}
                    join job_category_relations jcr on j.id = jcr.job_id
                    join job_category jc on jcr.category_code = jc.code
                    group by jc.name
                    order by 匹配數量 desc
                    limit 10;
                """
                rank_df = load_data(rank_sql, tuple(final_params))
                if not rank_df.empty:
                    rank_df['好去處'] = round((rank_df['匹配數量'] / total_jobs) * 100, 1).astype(str) + '%'
                    st.dataframe(rank_df, hide_index=True)
                else:
                    st.info("目前沒有足夠的資料分析職缺")
    elif page == '系統登入':
        st.title('系統後台登入')
        auth_mode = st.radio('請選擇操作', ['登入', '註冊新帳號'], horizontal=True)
        if auth_mode == '登入':
            login_user = st.text_input('帳號')
            login_password = st.text_input('密碼', type='password')
            if st.button('登入'):
                if login_user and login_password:
                    check_sql = "select password_hash from users where username = %s"
                    user_data = load_data(check_sql, (login_user,))
                    if not user_data.empty:
                        db_hash = user_data['password_hash'].iloc[0]
                        if verify_password(login_password, db_hash):
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = login_user
                            st.success('登入成功')
                            st.rerun()
                        else:
                            st.error('密碼錯誤')
                    else:
                        st.error('帳號錯誤')
                else:
                    st.warning('請輸入帳號與密碼')
        elif auth_mode == '註冊新帳號':
            reg_user = st.text_input('設定帳號')
            reg_password = st.text_input('設定密碼')
            sc = st.text_input('通關密碼', type='password')
            if st.button('確認註冊'):
                if not reg_user or not reg_password or not sc:
                    st.warning('所有欄位皆為必填')
                elif sc != os.getenv('SC'):
                    st.error('通關密碼錯誤, 繼續猜吧')
                else:
                    check_exist = load_data('select id from users where username = %s', (reg_user,))
                    if not check_exist.empty:
                        st.error('此帳號已被使用')
                    else:
                        hashed_password = hash_password(reg_password)
                        insert_sql = 'insert into users (username, password_hash) values (%s, %s)'
                        if execute_query(insert_sql, (reg_user, hashed_password)):
                            st.success('註冊成功, 請切換至登入頁面')
                        else:
                            st.error('系統發生錯誤')
    elif page == '職缺閱覽':
        st.title('歡迎來到地下寶庫')
        my_quote = quote('words.json')
        q_col1, q_col2 = st.columns([1, 4])
        with q_col1:
            st.image(my_quote['image'], use_container_width=True)
        with q_col2:
            st.markdown(
                f"<h3 style='font-style: italic; color: lightgray; border-left: 5px solid gray; padding-left: 15px;'>“{my_quote['text']}”</h3>",
                unsafe_allow_html=True
            )
        st.write('---')
        st.write('### 快速過濾')
        benefits_sql = 'select name from benefits'
        benefits_df = load_data(benefits_sql)
        benefits_list = benefits_df['name'].tolist()
        region_sql = 'select name from regions where level = 2'
        region_df = load_data(region_sql)
        region_list = region_df['name'].tolist()
        st.write('---')
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search_keyword = st.text_input('關鍵字搜尋 (職缺或公司名稱)')
        with col2:
            select_benefits = st.multiselect('要求福利', benefits_list)
        with col3:
            select_region = st.multiselect('縣市', region_list)
        with col4:
            only_no_exper = st.checkbox('無經驗可')
        dynamic_vip_joins = []
        vip_params = []
        if select_benefits:
            defense_bene = ', '.join(['%s'] * len(select_benefits))
            bene_sql = f"""
                join(
                    select jb.job_id
                    from job_benefits jb
                    join benefits b on jb.be_code = b.be_code
                    where b.name in ({defense_bene})
                    group by jb.job_id
                    having count(distinct b.name) = {len(select_benefits)}
                ) as match_be on j.id = match_be.job_id
             """
            dynamic_vip_joins.append(bene_sql)
            vip_params.extend(select_benefits)
        if select_region:
            protect_region = ', '.join(['%s'] * len(select_region))
            reg_sql = f"""
                join(
                    select code from regions where name in ({protect_region})
                    union
                    select r2.code from regions r1
                    join regions r2 on r1.code = r2.parent_code
                    where r1.name in ({protect_region})
                ) as match_reg on j.region_code = match_reg.code
            """
            dynamic_vip_joins.append(reg_sql)
            vip_params.extend(select_region)
            vip_params.extend(select_region)
        vip_join_string = '\n'.join(dynamic_vip_joins)
        vip_sql = f"""
            select
                r.name as 地區,
                c.name as 公司名稱,
                j.job_title as 職缺名稱,
                round(j.response_pr * 100, 0) as hr回覆率,
                case j.salary_type
                    when 1 then '面議'
                    when 2 then '論件'
                    when 3 then '時薪'
                    when 4 then '日薪'
                    when 5 then '月薪'
                    when 6 then '年薪'
                    else '未知'
                end as 支薪方式,
                j.salary_min as 最低薪資,
                j.salary_max as 最高薪資,
                group_concat(distinct s.name separator ', ') as 技能要求,
                group_concat(distinct b.name separator ', ') as 公司福利,
                j.link as 職缺連結
            from jobs j
            {vip_join_string}
            join company c on j.company_id = c.id
            left join regions r on j.region_code = r.code
            left join job_skills js on j.id = js.job_id
            left join skills s on js.skills_id = s.id
            left join job_benefits jb2 on j.id = jb2.job_id
            left join benefits b on jb2.be_code = b.be_code
            where 1 = 1
        """
        if search_keyword:
            vip_sql = vip_sql + " and (j.job_title like %s or c.name like %s)"
            vip_params.extend([f"%{search_keyword}%", f"%{search_keyword}%"])
        if only_no_exper:
            vip_sql = vip_sql + " and j.no_exper = 1"
        vip_sql += f"""
            group by j.id, r.name, c.name, j.job_title, j.response_pr, j.salary_type, j.salary_min, j.salary_max, j.link
            order by j.created_at desc
            limit 300;
        """
        vip_df = load_data(vip_sql, tuple(vip_params))
        if not vip_df.empty:
            st.write(f'共 **{len(vip_df)}** 筆結果(最多顯示100筆)')
            st.dataframe(
                vip_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    '職缺連結': st.column_config.LinkColumn('投遞連結', display_text='前往應徵'),
                    '最低薪資': st.column_config.NumberColumn(format="%d"),
                    "最高薪資": st.column_config.NumberColumn(format="%d"),
                    'hr回覆率': st.column_config.NumberColumn('回覆率', format='%d%%')
                }
            )
        else:
            st.info(f"請放寬搜尋標準")
except Exception as e:
    send_error(str(e), subject=f"streamlit本體出現問題: {e}")
    print(f"出問題囉 弟弟: {e}")