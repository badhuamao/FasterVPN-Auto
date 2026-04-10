import requests
import re

# 目标仓库列表
TARGET_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/all.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/singbox.json",
    "https://raw.githubusercontent.com/Whoahaow/rjsxrd/main/githubmirror/default/24.txt"
]

def harvest():
    raw_text = ""
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in TARGET_URLS:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                raw_text += resp.text + "\n"
        except:
            continue
    
    # 只要匹配到域名和2-5位数字端口就带走
    regex = r"([\w\d\.-]+?\.fastervpn\.world).*?[:\"'\s]+(\d{2,5})"
    matches = re.findall(regex, raw_text, re.IGNORECASE)
    
    final_nodes = []
    seen = set()
    
    for server, port in matches:
        uid = f"{server.lower()}:{port}"
        if uid not in seen:
            # 暴力转换格式
            node = f"{{name: '{server}', server: {server}, port: {port}, type: hysteria2, password: 'fastervpn.world', sni: {server}, skip-cert-verify: true}}"
            final_nodes.append(node)
            seen.add(uid)
            
    return final_nodes

if __name__ == "__main__":
    nodes = harvest()
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        if nodes:
            for n in nodes:
                f.write(f"  - {n}\n")
        else:
            f.write("  # No nodes found\n")
    print(f"Done. Found {len(nodes)} nodes.")
