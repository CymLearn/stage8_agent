# -*- coding: utf-8 -*-
# --------------------------------------------
# 项目名称: SerpApi搜索工具定义 
# --------------------------------------------


# 需要安装 SerpApi
# pip install google-search-results

import json
import requests
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()


import os
from serpapi import SerpApiClient
from typing import Dict, Any


# 我们的工具是 search 函数，它的作用是接收一个查询字符串，然后返回搜索结果。
def search(query: str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误：SERPAPI_API_KEY 未在 .env 文件中配置。"

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # 国家代码
            "hl": "zh-cn", # 语言代码
        }

        client = SerpApiClient(params)
        results = client.get_dict()
        print("results: ", json.dumps(results, ensure_ascii=False, indent=4))

        # print("【DEBUG】WEB search results: ", json.dumps(results, ensure_ascii=False, indent=4))
        
        if search_engine == "google":
            # 智能解析：优先寻找最直接的答案
            if "organic_results" in results and results["organic_results"]:
                # 如果没有直接答案，则返回前三个organic_results的摘要
                snippets = [
                        res.get('link', '') for i, res in enumerate(results["organic"][:limit])
                ]
                return snippets
        elif search_engine == "google_images":
            if "images_results" in results and results["images_results"]:
                snippets = [
                        res.get('original', '') for i, res in enumerate(results["images_results"][:limit])
                ]
                return snippets

        
        print(f"对不起，没有找到关于 '{query}' 的信息。")
        return []

    #except Exception as e:
    #    return f"搜索时发生错误: {e}"
    
if __name__ == '__main__':
    query = "英伟达最新的GPU型号是什么"
    print(f"\n--- 执行 Action: Search[{query}] ---")

    results = search(query)
    # results = search(query, search_engine="google_images")
    print("--- 搜索结果 (Results) ---")
    for i, res in enumerate(results):
        print(f"[{i+1}] {res}\n")
