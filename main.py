import requests
import re
import socket
import os

# 1. 填入你手动搜到的那些高质量“老巢”
TARGET_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/all.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/singbox.json",
    "https://raw.githubusercontent.com/Whoahaow/rjsxrd/main/githubmirror/default/24.txt"
]

def check_tcp(server, port):
    try:
        with socket.create_connection((server, int(port)), timeout=2):
            return True
    except:
        return False

def harvest():
    raw_text = ""
    for url in TARGET_URLS:
        try:
            print(f"[*] 正在突击仓库: {url}")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                raw_text += resp.text + "\n"
        except: continue
    
    # 2. 暴力提取：匹配域名+端口 (兼容 hysteria2://、JSON、YAML)
    # 只要域名是 fastervpn.world 且后面带着 1-5 位数字端口，直接带走
    regex = r"([\w\d\.-]+?\.fastervpn\.world).*?[:\"'\s]+(\d{2,5})"
    matches = re.findall(regex, raw_text, re.IGNORECASE)
    
    final_nodes = []
    seen_ids = set()
    
    for server, port in matches:
        server = server.strip().lower()
        port = port.strip()
        uid = f"{server}:{port}"
        
        if uid not in seen_ids:
            if check_tcp(server, port):
                print(f"[+] 活捉节点: {uid}")
                # 统一转换成你用的 Clash 格式
                node_yaml = (
                    f"{{name: '{server}', server: {server}, port: {port}, "
                    f"type: hysteria2, password: 'fastervpn.world', "
                    f"up: 20, down: 80, sni: {server}, skip-cert-verify: true}}"
                )
                final_nodes.append(node_yaml)
                seen_ids.add(uid)
    return final_nodes

if __name__ == "__main__":
    print("--- 针对性扫荡开始 ---")
    live_nodes = harvest()
    
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        if live_nodes:
            for n in live_nodes:
                f.write(f"  - {n}\n")
        else:
            f.write("  # 奇怪，连老巢都空了？请检查网络连接\n")
            
    print(f"--- 扫荡结束，共计活节点: {len(live_nodes)} ---")
