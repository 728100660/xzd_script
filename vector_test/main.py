import weaviate
import jieba
import time
import json
from datetime import datetime
from typing import Dict, List, Any

from weaviate.auth import AuthApiKey


auth = AuthApiKey("WVF5YThaHlkYwhGUSmCRgsX3tD5ngdN8pkih")
# 连接 Weaviate
client = weaviate.Client(
    url="http://localhost:8080",  # 替换为你的 Weaviate 地址
    auth_client_secret=auth
)


def init_test_vector():
    # 删除已有类
    if client.schema.exists("QAPair"):
        client.schema.delete_class("QAPair")

    # 创建 schema，增加 segmentedQuestion 字段
    schema = {
        "class": "QAPair",
        "vectorizer": "none",  # 使用 BM25，不用 embedding
        "properties": [
            {"name": "question", "dataType": ["text"]},
            {"name": "segmentedQuestion", "dataType": ["text"]},
            {"name": "answer", "dataType": ["text"]}
        ]
    }
    client.schema.create_class(schema)

    # 问答对数据
    qa_data = [
        ("什么是人工智能？", "人工智能是使计算机执行智能任务的技术。"),
        ("Python 是什么？", "Python 是一种高级编程语言。"),
        ("地球是圆的吗？", "是的，地球是一个近似球体。"),
        ("太阳从哪里升起？", "太阳从东方升起。"),
        ("水的沸点是多少？", "水的沸点是100摄氏度。"),
        ("中国的首都是哪里？", "中国的首都是北京。"),
        ("1+1等于几？", "1+1等于2。"),
        ("计算机的基本组成部分有哪些？", "包括输入设备、输出设备、CPU 和内存。"),
        ("世界上最高的山是哪座？", "珠穆朗玛峰是世界上最高的山。"),
        ("人类有多少颗牙齿？", "成年人一般有32颗牙齿。"),
    ]

    # 插入数据，附带分词字段
    for q, a in qa_data:
        segmented_q = " ".join(jieba.lcut(q+a))
        client.data_object.create(
            data_object={
                "question": q,
                "segmentedQuestion": segmented_q,
                "answer": a
            },
            class_name="QAPair"
        )

    time.sleep(2)  # 等待数据写入


def test_vector(query_texts: list[str]):
    # 执行 BM25 查询：在分词字段中查找，并且统计此次查询的耗时、返回结果数量
    results = []
    for query_text in query_texts:
        start_time = time.time()
        result = client.query.get("QAPair", ["question", "answer"]) \
            .with_bm25(query=query_text, properties=["segmentedQuestion", "question"]) \
            .with_limit(3) \
            .do()

        # 输出结果
        print("BM25 中文分词字段查询结果：")
        for item in result["data"]["Get"]["QAPair"]:
            print(f"- Q: {item['question']}")
            print(f"  A: {item['answer']}\n")

        results.append({
            "query_text": query_text,
            "time": time.time() - start_time,
            "result_count": len(result["data"]["Get"]["QAPair"]),
            "is_success": True if len(result["data"]["Get"]["QAPair"]) > 0 else False
        })

    return {
        "detail": results,
        "statistics": {
            "total_time": sum([result["time"] for result in results]),
            "total_result_count": sum([result["result_count"] for result in results]),
            "success_rate": sum([result["is_success"] for result in results]) / len(results)
        }
    }

def generate_test_report(test_results: Dict[str, Any], test_type: str) -> str:
    """生成测试报告"""
    report = f"""
# BM25搜索测试报告
测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
测试类型: {test_type}

## 总体统计
- 总查询数: {len(test_results['detail'])}
- 总耗时: {test_results['statistics']['total_time']:.3f}秒
- 平均每次查询耗时: {test_results['statistics']['total_time']/len(test_results['detail']):.3f}秒
- 查询成功率: {test_results['statistics']['success_rate']*100:.2f}%
- 总返回结果数: {test_results['statistics']['total_result_count']}
- 平均每次查询返回结果数: {test_results['statistics']['total_result_count']/len(test_results['detail']):.2f}

## 详细测试结果
"""
    for idx, result in enumerate(test_results['detail'], 1):
        report += f"""
### 测试用例 {idx}
- 查询文本: {result['query_text']}
- 查询耗时: {result['time']:.3f}秒
- 返回结果数: {result['result_count']}
- 查询是否成功: {'是' if result['is_success'] else '否'}
"""
    
    return report

def get_test_cases() -> Dict[str, List[str]]:
    """生成测试用例"""
    return {
        "基本功能测试": [
            "人工智能是什么",
            "Python编程",
            "地球形状",
        ],
        "精确匹配测试": [
            "什么是人工智能？",
            "Python 是什么？",
            "地球是圆的吗？",
        ],
        "部分匹配测试": [
            "智能",
            "编程语言",
            "地球",
        ],
        "边界测试": [
            # "",  # 空查询
            "？！@#￥%……&*（）",  # 特殊字符
            "这是一个非常非常非常非常非常非常非常非常非常非常非常非常非常长的查询" * 3,  # 超长查询
        ],
        "语义相关测试": [
            "机器智能",  # 同义词
            "计算机编程",  # 相关词
            "水温一百度",  # 近义表达
        ],
        "批量性能测试": [
            query for query in ["人工智能", "编程语言", "地球", "太阳", "水"] * 2  # 重复查询测试性能
        ]
    }

def main():
    while True:
        cmd = input("请输入命令(init/test/q)：")
        if cmd == "q":
            break
        if cmd == "init":
            init_test_vector()
        elif cmd == "test":
            cmd2 = input("请输入测试类型(1.单个查询 2.批量测试 3.完整测试套件 4.对query进行分词的完整测试套件)：")
            if cmd2 == "1":
                query_text = input("请输入查询内容：")
                results = test_vector([query_text])
                print(generate_test_report(results, "单个查询测试"))
            elif cmd2 == "2":
                query_count = int(input("请输入要测试的查询数量："))
                query_texts = [input(f"请输入第{i+1}个查询内容：") for i in range(query_count)]
                results = test_vector(query_texts)
                print(generate_test_report(results, "批量查询测试"))
            elif cmd2 == "3":
                test_cases = get_test_cases()
                for test_type, queries in test_cases.items():
                    print(f"\n执行{test_type}...")
                    results = test_vector(queries)
                    report = generate_test_report(results, test_type)
                    
                    # 保存测试报告到文件
                    filename = f"test_report_{test_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(report)
                    print(f"测试报告已保存到: {filename}")
            elif cmd2 == "4":
                test_cases = get_test_cases()
                for test_type, queries in test_cases.items():
                    print(f"\n执行{test_type}...")
                    segmented_queries = [" ".join(jieba.lcut(query)) for query in queries]
                    results = test_vector(segmented_queries)
                    report = generate_test_report(results, test_type)
                    
                    # 保存测试报告到文件
                    filename = f"test_report_segmented_{test_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(report)
                    print(f"测试报告已保存到: {filename}")
                    
            else:
                print("无效的测试类型！")

if __name__ == "__main__":
    main()
