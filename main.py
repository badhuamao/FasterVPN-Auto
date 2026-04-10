import requests
import re
import base64

# 搜索关键词
KEYWORD = "fastervpn.world"
# 搜索 GitHub 上的公开 YAML/JSON 配置
SEARCH_URL = f"https://api.github.com/search/code?q={KEYWORD}+extension:yaml+extension:json"

def fetch_nodes():
    headers = {"Accept": "application/vnd.github.v3+json"}
    # 注意：实际运行时建议在 Actions 中注入 GITHUB_TOKEN 以避免频率限制
    try:
        r = requests.get(SEARCH_URL, headers=headers)
        items = r.json().get('items', [])
        
        all_proxies = []
        for item in items:
            raw_url = item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            content = requests.get(raw_url).text
            # 这里的正则提取 H2 节点的关键信息 (简化版)
            nodes = re.findall(r"\{name:.*?" + KEYWORD + ".*?\}", content)
            all_proxies.extend(nodes)
            
        return all_proxies
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    proxies = fetch_nodes()
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        for p in list(set(proxies)): # 去重
            f.write(f"  - {p}\n")
    print(f"成功抓取到 {len(proxies)} 个候选节点")
