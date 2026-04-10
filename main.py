import requests
import re
import base64
import os

# 除了固定老巢，增加 GitHub 搜索 API
SEARCH_QUERY = 'fastervpn.world "hysteria2"'
TOKEN = os.getenv("MY_GITHUB_TOKEN")

TARGET_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/all.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/singbox.json",
    "https://raw.githubusercontent.com/Whoahaow/rjsxrd/main/githubmirror/default/24.txt"
]

def search_github():
    if not TOKEN:
        print("未检测到 Token，跳过全网搜索环节。")
        return []
    
    search_url = f"https://api.github.com/search/code?q={SEARCH_QUERY}"
    headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    found_urls = []
    try:
        r = requests.get(search_url, headers=headers, timeout=10)
        if r.status_code == 200:
            items = r.json().get('items', [])
            for item in items:
                # 转换成 raw 链接
                raw_url = item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                found_urls.append(raw_url)
    except:
        pass
    return found_urls

def harvest():
    final_nodes = []
    seen_uids = set()
    name_counts = {}
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 汇总固定源 + 搜索源
    all_sources = list(set(TARGET_URLS + search_github()))
    print(f"开始扫描，共 {len(all_sources)} 个源...")

    for url in all_sources:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200: continue
            content = resp.text
            
            # 兼容多种格式的通用正则表达式
            # 1. 链接格式
            links = re.findall(r"hysteria2://([^@]+)@([\w\d\.-]+?\.fastervpn\.world):(\d+)", content, re.I)
            # 2. 字段格式 (YAML/JSON)
            blocks = re.split(r'-\s+name:|{', content)
            
            # 处理链接
            for pwd, host, port in links:
                save_node(host, port, pwd, final_nodes, seen_uids, name_counts)
            
            # 处理块
            for block in blocks:
                if "fastervpn.world" in block:
                    h = re.search(r"([\w\d\.-]+?\.fastervpn\.world)", block)
                    p = re.search(r"(?:port|server_port)[:\"\s]+(\d+)", block)
                    pw = re.search(r"(?:password|auth_str)[:\"\s]+['\"]?([^'\"\s,{}]+)['\"]?", block)
                    if h and p:
                        save_node(h.group(1), p.group(1), pw.group(1) if pw else "test.+", final_nodes, seen_uids, name_counts)
        except: continue
    return final_nodes

def save_node(host, port, pwd, final_nodes, seen_uids, name_counts):
    uid = f"{host}:{port}:{pwd}"
    if uid not in seen_uids:
        base_name = host.split('.')[0] # 简化名称，只取前缀
        name_counts[base_name] = name_counts.get(base_name, 0) + 1
        display_name = f"{base_name}_{name_counts[base_name]}"
        node = f"{{name: '{display_name}', server: {host}, port: {port}, type: hysteria2, password: '{pwd}', sni: {host}, skip-cert-verify: true}}"
        final_nodes.append(node)
        seen_uids.add(uid)

if __name__ == "__main__":
    nodes = harvest()
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        for n in nodes: f.write(f"  - {n}\n")
    print(f"收割完成，本次产出 {len(nodes)} 个节点。")
