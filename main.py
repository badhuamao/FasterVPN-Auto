import requests
import re
import socket
import concurrent.futures

# 1. 整理出的高概率包含 FasterVPN 的原始订阅源
# 这些源包含了从 GitHub、Telegram 采集的各种明文节点
DIRECT_SOURCES = [
    "https://raw.githubusercontent.com/vpei/Free-Node-Merge/refs/heads/main/clash.yaml",
    "https://raw.githubusercontent.com/mS_one/oneclickvpnkeys/refs/heads/main/singbox.json",
    "https://raw.githubusercontent.com/anaer/Sub/master/clash.yaml",
    "https://raw.githubusercontent.com/tina-v1/tina-nodes/refs/heads/main/all_nodes.yaml",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/source/clash.yaml"
]

def check_tcp(server, port):
    try:
        with socket.create_connection((server, int(port)), timeout=2):
            return True
    except:
        return False

def fetch_all_raw():
    all_text = ""
    for url in DIRECT_SOURCES:
        try:
            print(f"[*] 正在收割源: {url}")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                all_text += resp.text + "\n"
        except:
            continue
    return all_text

def extract_and_verify(content):
    # 暴力匹配所有 fastervpn.world 相关行
    # 无论是 JSON 还是 YAML 格式，提取域名和端口
    regex = r"([\w\d\.-]+?\.fastervpn\.world)[\s:：\"']+?(\d+)"
    matches = re.findall(regex, content, re.IGNORECASE)
    
    unique_ids = set()
    final_proxies = []

    # 这里的匹配结果是 (域名, 端口)
    for server, port in matches:
        server = server.strip().strip("'").strip('"').lower()
        port = port.strip()
        uid = f"{server}:{port}"
        
        if uid not in unique_ids:
            if check_tcp(server, port):
                print(f"[+] 活的! {uid}")
                # 按照标准 Hysteria2 格式拼装
                node = (
                    f"{{name: '{server}', server: {server}, port: {port}, "
                    f"type: hysteria2, password: 'fastervpn.world', "
                    f"up: 20, down: 80, sni: {server}, skip-cert-verify: true}}"
                )
                final_proxies.append(node)
                unique_ids.add(uid)
            else:
                print(f"[-] 挂了: {uid}")
                
    return final_proxies

if __name__ == "__main__":
    print("--- 定向收割启动 ---")
    raw_data = fetch_all_raw()
    nodes = extract_and_verify(raw_data)
    
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        if nodes:
            for n in nodes:
                f.write(f"  - {n}\n")
        else:
            f.write("  # 看来这几个老巢今天也没货，老友明天再来\n")
            
    print(f"--- 任务结束，共捕获活节点: {len(nodes)} ---")
