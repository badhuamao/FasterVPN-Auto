import requests
import re
import os
import socket

# 搜索与收割源配置
SEARCH_QUERY = 'fastervpn.world "hysteria2"'
TOKEN = os.getenv("MY_GITHUB_TOKEN")

TARGET_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/all.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/singbox.json",
    "https://raw.githubusercontent.com/Whoahaow/rjsxrd/main/githubmirror/default/24.txt"
]

def is_domain_resolvable(domain):
    """基础过滤：检查域名是否还在世（是否能解析出IP）"""
    try:
        socket.gethostbyname(domain)
        return True
    except:
        return False

def search_github():
    if not TOKEN: return []
    # 增加排序，确保拿到最新被索引的内容
    search_url = f"https://api.github.com/search/code?q={SEARCH_QUERY}&sort=indexed&order=desc"
    headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    found_urls = []
    try:
        r = requests.get(search_url, headers=headers, timeout=10)
        if r.status_code == 200:
            for item in r.json().get('items', []):
                raw_url = item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                found_urls.append(raw_url)
    except: pass
    return found_urls

def harvest():
    final_nodes = []
    seen_uids = set()
    name_counts = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    all_sources = list(set(TARGET_URLS + search_github()))
    print(f"[*] 开始扫描 {len(all_sources)} 个源...")

    for url in all_sources:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200: continue
            content = resp.text
            
            # 1. 链接提取
            links = re.findall(r"hysteria2://([^@]+)@([\w\d\.-]+?\.fastervpn\.world):(\d+)", content, re.I)
            for pwd, host, port in links:
                save_node(host, port, pwd, final_nodes, seen_uids, name_counts)
            
            # 2. 字段提取 (YAML/JSON)
            blocks = re.split(r'-\s+name:|{', content)
            for block in blocks:
                if "fastervpn.world" in block:
                    h = re.search(r"([\w\d\.-]+?\.fastervpn\.world)", block)
                    p = re.search(r"(?:port|server_port)[:\"\s]+(\d+)", block)
                    pw = re.search(r"(?:password|auth_str|auth)[:\"\s]+['\"]?([^'\"\s,{}]+)['\"]?", block)
                    if h and p:
                        save_node(h.group(1), p.group(1), pw.group(1) if pw else "test.+", final_nodes, seen_uids, name_counts)
        except: continue
    return final_nodes

def save_node(host, port, pwd, final_nodes, seen_uids, name_counts):
    pwd = pwd.strip().strip("'").strip('"').split(',')[0]
    uid = f"{host}:{port}:{pwd}"
    
    if uid not in seen_uids:
        # 核心改动：如果域名连解析都不行，说明已经彻底失效，直接跳过
        if not is_domain_resolvable(host):
            print(f"[-] 跳过已失效域名: {host}")
            return

        base_name = host.split('.')[0]
        name_counts[base_name] = name_counts.get(base_name, 0) + 1
        display_name = f"{base_name}_{name_counts[base_name]}"
        node = f"{{name: '{display_name}', server: {host}, port: {port}, type: hysteria2, password: '{pwd}', sni: {host}, skip-cert-verify: true}}"
        final_nodes.append(node)
        seen_uids.add(uid)
        print(f"[+] 有效节点入库: {display_name}")

if __name__ == "__main__":
    nodes = harvest()
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        for n in nodes: f.write(f"  - {n}\n")
    print(f"收割完成！本次共保留有效节点 {len(nodes)} 个。")
