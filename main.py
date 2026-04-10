import requests
import re
import os
import socket
from concurrent.futures import ThreadPoolExecutor

SEARCH_QUERY = 'fastervpn.world "hysteria2"'
TOKEN = os.getenv("MY_GITHUB_TOKEN")
TARGET_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/all.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/singbox.json",
    "https://raw.githubusercontent.com/Whoahaow/rjsxrd/main/githubmirror/default/24.txt"
]

def check_port(node_info):
    host, port, pwd, node_str = node_info
    try:
        # 仅给 1.5 秒机会，不行就当做“疑似不可用”
        with socket.create_connection((host, int(port)), timeout=1.5):
            return True, node_str
    except:
        return False, node_str

def harvest():
    raw_candidates = []
    seen_uids = set()
    name_counts = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 获取所有源
    all_sources = list(set(TARGET_URLS))
    if TOKEN:
        try:
            r = requests.get(f"https://api.github.com/search/code?q={SEARCH_QUERY}", 
                             headers={"Authorization": f"token {TOKEN}"}, timeout=5)
            if r.status_code == 200:
                for item in r.json().get('items', []):
                    all_sources.append(item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/"))
        except: pass

    for url in all_sources:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200: continue
            # 提取 域名, 端口, 密码
            matches = re.findall(r"([\w\d\.-]+?\.fastervpn\.world).+?(\d{2,5}).+?['\"]?([^'\"\s,{}]{10,})['\"]?", resp.text)
            for host, port, pwd in matches:
                uid = f"{host}:{port}:{pwd}"
                if uid not in seen_uids:
                    seen_uids.add(uid)
                    base_name = host.split('.')[0]
                    name_counts[base_name] = name_counts.get(base_name, 0) + 1
                    node_str = f"{{name: '{base_name}_{name_counts[base_name]}', server: {host}, port: {port}, type: hysteria2, password: '{pwd}', sni: {host}, skip-cert-verify: true}}"
                    raw_candidates.append((host, port, pwd, node_str))
        except: continue
    
    # 使用线程池并发测速
    live_nodes = []
    maybe_dead_nodes = []
    print(f"[*] 正在并发探测 {len(raw_candidates)} 个节点...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_port, raw_candidates))
    
    for is_live, node_str in results:
        if is_live:
            live_nodes.append(node_str)
        else:
            maybe_dead_nodes.append(node_str)
            
    return live_nodes, maybe_dead_nodes

if __name__ == "__main__":
    live, maybe_dead = harvest()
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        # 先写活的
        for n in live: f.write(f"  - {n}\n")
        # 再写不确定的（不加注释，直接放进去，防止误杀）
        for n in maybe_dead: f.write(f"  - {n}\n")
    
    print(f"完成！检测到通畅节点: {len(live)} 个，疑似阻塞节点: {len(maybe_dead)} 个。全部已入库。")
