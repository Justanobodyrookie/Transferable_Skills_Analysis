user_lang_levels = {'英文': '中等'}
level_accept_map = {
    "不拘": [0],
    "略懂": [0, 4],
    "中等": [0, 4, 8],
    "精通": [0, 4, 8, 2]
}

lang_conditions = []
lang_params = []

for lang, level_text in user_lang_levels.items():
    acc_code = level_accept_map[level_text]
    defense = ', '.join(['%s'] * len(acc_code))
    step1 = f"(language_name = %s and level in ({defense}))"
    lang_conditions.append(step1)
    lang_params.append(lang)
    lang_params.extend(acc_code)
    print(lang_params)
final_lang_sql = " or ".join(lang_conditions)
print(final_lang_sql)