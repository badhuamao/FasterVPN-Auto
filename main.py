import requests
import re

# 定向精准源
SOURCES = [
    "https://raw.githubusercontent.com/mS_one/oneclickvpnkeys/refs/heads/main/singbox.json",
    "https://raw.githubusercontent.com/vpei/Free-Node-Merge/refs/heads/main/clash.yaml",
    "https://raw.githubusercontent.com/tina-v1/tina-nodes/refs/heads/main/all_nodes.yaml",
    "https://api.v1.mk/sub?target=clash&url=https://raw.githubusercontent.com/mS_one/oneclickvpnkeys/refs/heads/main/singbox.json"
]

def extract_nodes():
    all_content = ""
    for url in SOURCES:
        try:
            print(f"[*] 正在扫描源: {url}")
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                all_content += resp.text + "\n"
        except Exception as e:
            print(f"[!] 无法连接 {url}: {e}")

    # 重点：匹配 FasterVPN 的 Hysteria2 节点行
    # 匹配模式：- {name: ..., server: vpn-xxx.fastervpn.world, ... type: hysteria2 ...}
    pattern = r"-\s*\{name:[^}]*?fastervpn\.world[^}]*?type:\s*hysteria2[^}]*?\}"
    nodes = re.findall(pattern, all_content, re.IGNORECASE)
    
    # 简单的去重处理
    unique_nodes = list(set(nodes))
    return unique_nodes

if __name__ == "__main__":
    nodes = extract_nodes()
    print(f"[+] 捕获到 {len(nodes)} 个有效的 FasterVPN 节点")
    
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        if nodes:
            for n in nodes:
                # 清洗一下格式，确保缩进正确
                clean_node = n.strip().lstrip('-').strip()
                f.write(f"  - {clean_node}\n")
        else:
            f.write("  # 此时此刻没抓到，老友别急，等下次更新\n")
