import requests
import re
import os

# 依然守住这几个确定的老巢
TARGET_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/all.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/singbox.json",
    "https://raw.githubusercontent.com/Whoahaow/rjsxrd/main/githubmirror/default/24.txt"
]

def harvest():
    final_nodes = []
    seen_uids = set()
    name_counts = {}
    headers = {'User-Agent': 'Mozilla/5.0'}

    for url in TARGET_URLS:
        try:
            print(f"[*] 正在收割: {url}")
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200: continue
            content = resp.text
            
            # 1. 专门抓取 hysteria2:// 链接格式 (这种格式最不容易出错)
            links = re.findall(r"hysteria2://([^@]+)@([\w\d\.-]+?\.fastervpn\.world):(\d+)", content, re.I)
            for pwd, host, port in links:
                uid = f"{host}:{port}:{pwd}"
                if uid not in seen_uids:
                    save_node(host, port, pwd, final_nodes, seen_uids, name_counts)

            # 2. 专门对付 YAML/JSON 的块提取
            # 逻辑：先找域名，再在附近找密码
            blocks = re.split(r'-\s+name:|{', content)
            for block in blocks:
                if "fastervpn.world" in block:
                    h_m = re.search(r"([\w\d\.-]+?\.fastervpn\.world)", block)
                    p_m = re.search(r"(?:port|server_port)[:\"\s]+(\d+)", block)
                    # 密码正则加强：允许包含特殊字符，直到遇到引号、空格或逗号为止
                    pw_m = re.search(r"(?:password|auth_str)[:\"\s]+['\"]?([^'\"\s,{}]+)['\"]?", block)
                    
                    if h_m and p_m:
                        host = h_m.group(1).lower()
                        port = p_m.group(1)
                        pwd = pw_m.group(1) if pw_m else "test.+"
                        save_node(host, port, pwd, final_nodes, seen_uids, name_counts)
        except: continue
            
    return final_nodes

def save_node(host, port, pwd, final_nodes, seen_uids, name_counts):
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
        if nodes:
            for n in nodes:
                f.write(f"  - {n}\n")
        else:
            f.write("  # 节点收割失败\n")
    print(f"收割完成，共抓取 {len(nodes)} 个节点，已存入 proxies.yaml")
