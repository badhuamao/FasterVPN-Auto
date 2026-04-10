import requests
import re
import os
import socket

SEARCH_QUERY = 'fastervpn.world "hysteria2"'
TOKEN = os.getenv("MY_GITHUB_TOKEN")

TARGET_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/all.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/singbox.json",
    "https://raw.githubusercontent.com/Whoahaow/rjsxrd/main/githubmirror/default/24.txt"
]

def check_port(host, port):
    """尝试连接端口，判断服务是否起码在运行"""
    try:
        with socket.create_connection((host, int(port)), timeout=3):
            return True
    except:
        return False

def harvest():
    final_nodes = []
    dead_nodes = []
    seen_uids = set()
    name_counts = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 汇总源链接
    all_sources = list(set(TARGET_URLS))
    if TOKEN:
        # 尝试搜索更多源
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
            # 暴力提取所有符合特征的组合
            matches = re.findall(r"([\w\d\.-]+?\.fastervpn\.world).+?(\d{2,5}).+?['\"]?([^'\"\s,{}]{10,})['\"]?", resp.text)
            
            for host, port, pwd in matches:
                uid = f"{host}:{port}:{pwd}"
                if uid not in seen_uids:
                    seen_uids.add(uid)
                    base_name = host.split('.')[0]
                    name_counts[base_name] = name_counts.get(base_name, 0) + 1
                    node_str = f"{{name: '{base_name}_{name_counts[base_name]}', server: {host}, port: {port}, type: hysteria2, password: '{pwd}', sni: {host}, skip-cert-verify: true}}"
                    
                    # 探测存活
                    if check_port(host, port):
                        final_nodes.append(node_str)
                    else:
                        dead_nodes.append(f"# [Dead] {node_str}")
        except: continue
    return final_nodes, dead_nodes

if __name__ == "__main__":
    live, dead = harvest()
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        for n in live: f.write(f"  - {n}\n")
        f.write("\n# 以下为探测失败节点，仅供参考\n")
        for n in dead: f.write(f"{n}\n")
    print(f"收割完毕：活节点 {len(live)} 个，死节点 {len(dead)} 个。")
