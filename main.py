import requests
import re
import socket
import concurrent.futures
import os

TOKEN = os.environ.get("MY_GITHUB_TOKEN")

def check_tcp(server, port):
    try:
        with socket.create_connection((server, int(port)), timeout=2):
            return True
    except:
        return False

def search_github():
    if not TOKEN: return ""
    url = "https://api.github.com/search/code?q=fastervpn.world+extension:yaml+extension:json+extension:txt"
    headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    combined_content = ""
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            items = resp.json().get('items', [])
            for item in items:
                raw_url = item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                try:
                    combined_content += requests.get(raw_url, timeout=5).text + "\n"
                except: continue
    except: pass
    return combined_content

def extract_nodes(content):
    # 【核心逻辑】直接通过正则把域名和端口抠出来，不再管大括号
    # 匹配 vpn-xxx.fastervpn.world:443 这种特征
    matches = re.findall(r"(vpn-[\w\d\.-]+?\.fastervpn\.world)[:：](\d+)", content, re.IGNORECASE)
    
    final_nodes = []
    seen_ids = set()
    
    for server, port in matches:
        unique_id = f"{server}:{port}"
        if unique_id not in seen_ids:
            if check_tcp(server, port):
                print(f"[+] 活节点捕获: {server}")
                # 手动拼装成你需要的 Clash 格式
                node_yaml = f"{{name: {server}, server: {server}, port: {port}, type: hysteria2, up: 30, down: 100, password: fastervpn.world, sni: {server}, skip-cert-verify: true}}"
                final_nodes.append(node_yaml)
                seen_ids.add(unique_id)
    return final_nodes

if __name__ == "__main__":
    raw_data = search_github()
    live_nodes = extract_nodes(raw_data)
    
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        if live_nodes:
            for node in live_nodes:
                f.write(f"  - {node}\n")
        else:
            f.write("  # 还是没抓到，可能这些节点刚好都挂了\n")
    print(f"任务结束，活节点: {len(live_nodes)}")
