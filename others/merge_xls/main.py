import pandas as pd

# 读取 Excel 时，强制把 ID 列当作字符串，避免科学计数法
df_m = pd.read_excel("sys_user_m.xlsx", dtype={"user_id": str})
df_p = pd.read_excel("sys_user_p.xlsx", dtype={"用户ID": str})

# 按 sys_user_p 的顺序进行匹配（how="left" 保留顺序）
merged = pd.merge(
    df_p,
    df_m,
    left_on="用户ID",
    right_on="user_id",
    how="left",
    sort=False
)

# 找出 sys_user_m 中没有匹配到的行（保持 m 的原有顺序）
unmatched = df_m[~df_m["user_id"].isin(df_p["用户ID"])]

# 合并结果：先是 p 的顺序，后是 m 未匹配的顺序
final_result = pd.concat([merged, unmatched], ignore_index=True)

# 保存时禁用科学计数法
with pd.ExcelWriter("合并结果.xlsx", engine="xlsxwriter") as writer:
    final_result.to_excel(writer, index=False)
    workbook  = writer.book
    worksheet = writer.sheets["Sheet1"]

    # 对所有列设置文本格式，防止数字转科学计数法
    text_fmt = workbook.add_format({"num_format": "@"})
    worksheet.set_column(0, len(final_result.columns)-1, None, text_fmt)

print("✅ 合并完成，已保持 sys_user_p 原顺序，并禁用科学计数法。")
