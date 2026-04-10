import requests
import re
import socket
import concurrent.futures

# 1. 增加更多源，包括一些自动生成的聚合订阅
SOURCES = [
    "https://raw.githubusercontent.com/mS_one/oneclickvpnkeys/refs/heads/main/singbox.json",
    "https://raw.githubusercontent.com/vpei/Free-Node-Merge/refs/heads/main/clash.yaml",
    "https://raw.githubusercontent.com/tina-v1/tina-nodes/refs/heads/main/all_nodes.yaml",
    "https://raw.githubusercontent.com/anaer/Sub/master/clash.yaml",
    "https://api.v1.mk/sub?target=clash&url=https://raw.githubusercontent.com/mS_one/oneclickvpnkeys/refs/heads/main/singbox.json"
]

def check_tcp(server, port):
    try:
        with socket.create_connection((server, int(port)), timeout=2):
            return True
    except:
        return False

def fetch_content():
    all_text = ""
    for url in SOURCES:
        try:
            print(f"[*] 正在爬取: {url}")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                all_text += resp.text + "\n"
        except: pass
    return all_text

def extract_nodes(content):
    # 更加宽松的正则：抓取所有包含 fastervpn.world 的 hysteria2 节点行
    # 无论是 {name: ...} 格式还是普通的 YAML 格式
    pattern = r"-\s*\{[^}]*?server:\s*([^, ]*?fastervpn\.world[^, ]*?)[^}]*?type:\s*hysteria2[^}]*?\}"
    nodes = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
    
    # 重新提取完整的节点块（防止正则截断）
    final_nodes = []
    seen_servers = set()
    
    # 二次匹配，确保拿到的是完整的 YAML 对象
    blocks = re.findall(r"-\s*\{[^}]*?fastervpn\.world[^}]*?\}", content)
    
    for block in blocks:
        # 提取 server 和 port 用于去重和测速
        s_match = re.search(r"server:\s*([^, \}\n\r]+)", block)
        p_match = re.search(r"port:\s*(\d+)", block)
        
        if s_match and p_match:
            server = s_match.group(1).strip()
            port = p_match.group(2).strip()
            unique_id = f"{server}:{port}"
            
            if unique_id not in seen_servers:
                # 在云端简单测速
                if check_tcp(server, port):
                    print(f"[+] 活的节点: {server}")
                    final_nodes.append(block)
                    seen_servers.add(unique_id)
                else:
                    print(f"[-] 死的节点: {server}")
    
    return final_nodes

if __name__ == "__main__":
    raw_content = fetch_content()
    live_nodes = extract_nodes(raw_content)
    
    print(f"\n[!] 最终捕获到 {len(live_nodes)} 个可用节点")
    
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        for node in live_nodes:
            # 统一格式处理
            line = node.strip().lstrip('-').strip()
            f.write(f"  - {line}\n")
