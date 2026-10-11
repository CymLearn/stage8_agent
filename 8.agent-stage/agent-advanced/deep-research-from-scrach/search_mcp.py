# -*- coding: utf-8 -*-
# --------------------------------------------
# 项目名称: 深度研究智能体MCP工具代码
# --------------------------------------------


import os
from mcp.server.fastmcp import FastMCP
import requests
from openai import OpenAI
import logging
import tools 


mcp = FastMCP("search")


# 创建日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# 创建文件处理器
file_handler = logging.FileHandler('test.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

client = OpenAI(
            base_url=os.getenv("BASE_URL"),
            api_key=os.getenv("API_KEY")
        )


def generate_query(query, stream=False):
    prompt ="""You are an expert research assistant. Given the user's query, generate up to four distinct, precise search queries that would help gather comprehensive information on the topic.
    Return only a Python list of strings, for example: ['query1', 'query2', 'query3']."""

    response = client.chat.completions.create(
                    model=os.getenv("MODEL_ID"),
                    messages = [
        {"role": "system", "content": "You are a helpful and precise research assistant."},
        {"role": "user", "content": f"User Query: {query}\n\n{prompt}"}
    ]
                )
    return response.choices[0].message.content


def if_useful(query: str, page_text: str):
    prompt ="""You are a critical research evaluator. Given the user's query and the content of a webpage, determine if the webpage contains information relevant and useful for addressing the query.
    Respond with exactly one word: 'Yes' if the page is useful, or 'No' if it is not. Do not include any extra text."""

    response = client.chat.completions.create(
                    model=os.getenv("MODEL_ID"),
                    messages = [
        {"role": "system", "content": "You are a strict and concise evaluator of research relevance."},
        {"role": "user", "content": f"User Query: {query}\n\nWebpage Content (first 20000 characters):\n{page_text[:20000]}\n\n{prompt}"}
    ]
                )

    response = response.choices[0].message.content

    if response:
        answer = response.strip()
        if answer in ["Yes", "No"]:
            return answer
        else:
            # Fallback: try to extract Yes/No from the response.
            if "Yes" in answer:
                return "Yes"
            elif "No" in answer:
                return "No"
    return "No"

def extract_relevant_context(query, search_query, page_text): # 上下文工程管理
    prompt ="""You are an expert information extractor. Given the user's query, the search query that led to this page, and the webpage content, extract all pieces of information that are relevant to answering the user's query.
    Return only the relevant context as plain text without commentary."""

    response = client.chat.completions.create(
                    model=os.getenv("MODEL_ID"),
                    messages = [
        {"role": "system", "content": "You are an expert in extracting and summarizing relevant information."},
        {"role": "user", "content": f"User Query: {query}\nSearch Query: {search_query}\n\nWebpage Content (first 20000 characters):\n{page_text[:20000]}\n\n{prompt}"}
    ]
                )

    response = response.choices[0].message.content
    if response:
        return response.strip()
    return ""

def get_new_search_queries(user_query, previous_search_queries, all_contexts):
    context_combined = "\n".join(all_contexts)
    prompt ="""You are an analytical research assistant. Based on the original query, the search queries performed so far, and the extracted contexts from webpages, determine if further research is needed.
    If further research is needed, provide up to four new search queries as a Python list (for example, ['new query1', 'new query2']). If you believe no further research is needed, respond with exactly .
    Output only a Python list or the token  without any additional text."""

    response = client.chat.completions.create(
                    model=os.getenv("MODEL_ID"),
                    messages = [
        {"role": "system", "content": "You are a helpful and precise research assistant."},
        {"role": "user", "content": f"User Query: {user_query}\nPrevious Search Queries: {previous_search_queries}\n\nExtracted Relevant Contexts:\n{context_combined}\n\n{prompt}"}
    ]
                )

    response = response.choices[0].message.content
    if response:
        cleaned = response.strip()
        if cleaned == "":
            return ""
        try:
            new_queries = eval(cleaned)
            if isinstance(new_queries, list):
                return new_queries
            else:
                logger.info(f"LLM did not return a list for new search queries. Response: {response}")
                return []
        except Exception as e:
            logger.error(f"Error parsing new search queries:{e}, Response:{response}")
            return []
    return []


def fetch_webpage_text(url):
    JINA_BASE_URL = 'https://r.jina.ai/'
    full_url = f"{JINA_BASE_URL}{url}"
    
    try:
        resp = requests.get(full_url, timeout=50)
        if resp.status_code == 200:
            return resp.text
        else:
            text = resp.text
            logger.info(f"Jina fetch error for {url}: {resp.status_code} - {text}")
            return ""
    except Exception as e:
        logger.error(f"Error fetching webpage text with Jina:{e}")
        return ""


def process_link(link, query, search_query):
    logger.info(f"Fetching content from: {link}")
    page_text = fetch_webpage_text(link)
    if not page_text:
        return None
    usefulness = if_useful(query, page_text)
    logger.info(f"Page usefulness for {link}: {usefulness}")
    if usefulness == "Yes":
        context = extract_relevant_context(query, search_query, page_text)
        if context:
            logger.info(f"Extracted context from {link} (first 200 chars): {context[:200]}")
            return context
    return None


def get_images_description(iamge_url):
    completion = client.chat.completions.create(
    
    model="qwen3-vl-flash",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "使用一句话描述图片的内容"
            },
            {
            "type": "image_url",
            "image_url": {
                "url": iamge_url
            }
            }
        ]
        }
    ]
    )
    return completion.choices[0].message.content

@mcp.tool()
def search(query: str) -> str:
    """文本搜索：根据提供的搜索词从web上搜索并返回相关的文本内容"""
    iteration_limit = 3
    iteration = 0
    aggregated_contexts = []  
    all_search_queries = []   
    iteration = 0
    
    new_search_queries = eval(generate_query(query))
    all_search_queries.extend(new_search_queries)

    # add the original query to the search queries in case it is not already in the list
    if query not in all_search_queries:
        all_search_queries.append(query)
    while iteration < iteration_limit:
            logger.info(f"\n=== Iteration {iteration + 1} ===")
            iteration_contexts = []
            search_results = [tools.search(query, search_engine="google", limit=2) for query in new_search_queries] # urls

            unique_links = {}
            for idx, links in enumerate(search_results):
                search_query = new_search_queries[idx]  # prevent the query being replaced as the Search parameter
                for link in links:
                    if link not in unique_links:
                        unique_links[link] = search_query

            logger.info(f"Aggregated {len(unique_links)} unique links from this iteration.")

            # Process each link concurrently: fetch, judge, and extract context.
            link_results = [
                process_link(link, query, unique_links[link])
                for link in unique_links
            ]
            
            # Collect non-None contexts.
            for res in link_results:
                if res:
                    iteration_contexts.append(res)

            if iteration_contexts:
                aggregated_contexts.extend(iteration_contexts)
            else:
                logger.info("No useful contexts were found in this iteration.")

            new_search_queries = get_new_search_queries(query, all_search_queries, aggregated_contexts)
            if new_search_queries == "":
                logger.info("LLM indicated that no further research is needed.")
                break
            elif new_search_queries:
                logger.info(f"LLM provided new search queries:{new_search_queries}")
                all_search_queries.extend(new_search_queries)
            else:
                logger.info("LLM did not provide any new search queries. Ending the loop.")
                break

            iteration += 1
    return '\n\n'.join(aggregated_contexts)

@mcp.tool()
def get_images(query: str) -> str:
    '''图片搜索：根据提供的搜索词从web上搜索相关的图片并返回图片的内容描述'''
    logger.info(f"Searching for images for query: {query}")
    # Get image links directly through web_search function
    img_srcs = tools.search(query, search_engine="google_images", limit=2)

    result = {}
    for img_src in img_srcs:
        try:
            logger.info(f"Fetching image description for: {img_src}")
            description = get_images_description(img_src)
            logger.info(f"Image description for {img_src}: {description}")
            result[img_src] = description
        except Exception:
            logger.info(f"LLM cannot parse the image url:{img_src}")

        
    # return "\n\n".join(result.values())
    return result
    
  

if __name__ == "__main__":
    mcp.run()
