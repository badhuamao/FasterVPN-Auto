import requests
import re
import os

# 1. 搜索与收割源配置
SEARCH_QUERY = 'fastervpn.world "hysteria2"'
TOKEN = os.getenv("MY_GITHUB_TOKEN")

# 这里填入你图中找到的那些高质量 Raw 链接
TARGET_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/all.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/singbox.json",
    "https://raw.githubusercontent.com/Whoahaow/rjsxrd/main/githubmirror/default/24.txt",
    # 建议把你在图中看到的新仓库 Raw 地址也加在这里
]

def search_github():
    if not TOKEN: return []
    search_url = f"https://api.github.com/search/code?q={SEARCH_QUERY}&sort=indexed"
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
    
    # 汇总源
    all_sources = list(set(TARGET_URLS + search_github()))
    
    for url in all_sources:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200: continue
            content = resp.text
            
            # 兼容模式：直接抓取 hysteria2:// 链接
            links = re.findall(r"hysteria2://([^@]+)@([\w\d\.-]+?\.fastervpn\.world):(\d+)", content, re.I)
            for pwd, host, port in links:
                save_node(host, port, pwd, final_nodes, seen_uids, name_counts)
            
            # 兼容模式：针对 YAML/JSON 的块提取
            blocks = re.split(r'-\s+name:|{', content)
            for block in blocks:
                if "fastervpn.world" in block:
                    h = re.search(r"([\w\d\.-]+?\.fastervpn\.world)", block)
                    p = re.search(r"(?:port|server_port)[:\"\s]+(\d+)", block)
                    # 增加对 auth_str, password 等字段的捕获
                    pw = re.search(r"(?:password|auth_str|auth)[:\"\s]+['\"]?([^'\"\s,{}]+)['\"]?", block)
                    if h and p:
                        save_node(h.group(1), p.group(1), pw.group(1) if pw else "test.+", final_nodes, seen_uids, name_counts)
        except: continue
    return final_nodes

def save_node(host, port, pwd, final_nodes, seen_uids, name_counts):
    # 密码清理，防止带入多余字符
    pwd = pwd.strip().strip("'").strip('"').split(',')[0]
    uid = f"{host}:{port}:{pwd}"
    if uid not in seen_uids:
        base_name = host.split('.')[0]
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
    print(f"收割完成！本次共斩获 {len(nodes)} 个节点。")
