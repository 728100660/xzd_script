import json
import csv

# 假设结构文件为结构如下
with open("scheme.txt", "r", encoding="utf-8") as f:
    json_data = json.load(f)


def general_each_table():
    # 遍历每个表，生成对应的CSV
    for table_name, table_def in json_data.items():
        csv_filename = f"{table_name}.csv"
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # 写表的基本信息（可选）
            writer.writerow([f"Table: {table_name}"])
            writer.writerow([])

            # 写列头
            writer.writerow(["Column Name", "Type", "Nullable", "Default", "Comment", "Is Primary Key"])

            # 构建主键集合便于判断
            primary_keys = set(table_def.get("primary_keys", []))

            for col in table_def.get("columns", []):
                writer.writerow([
                    col["name"],
                    col["type"],
                    "NO" if not col["nullable"] else "YES",
                    col["default"],
                    col["comment"],
                    "YES" if col["name"] in primary_keys else ""
                ])

            print(f"Table '{table_name}' written to {csv_filename}")


def to_one_file():
    # 打开 CSV 文件准备写入
    with open("tables_summary.csv", mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # 写标题
        writer.writerow(["table_name", "columns"])

        for table_name, table_def in json_data.items():
            primary_keys = set(table_def.get("primary_keys", []))

            # 拼接列信息
            columns_desc = []
            for col in table_def.get("columns", []):
                col_parts = [
                    col["name"],
                    col["type"],
                    "NOT NULL" if not col.get("nullable", True) else "NULL",
                    f"DEFAULT={col.get('default')}" if col.get("default") is not None else "",
                    "PK" if col["name"] in primary_keys else ""
                ]
                # 去除空字符串项，再用冒号拼接
                col_str = ":".join([p for p in col_parts if p])
                columns_desc.append(col_str)

            # 将所有列拼接为一个字符串，用 ; 分隔
            columns_combined = "; ".join(columns_desc)

            # 写入表名和列信息
            writer.writerow([table_name, columns_combined])

    print("✅ 所有表结构已写入 tables_summary.csv")


if __name__ == '__main__':
    to_one_file()
