import requests
import re

TARGET_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/all.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/singbox.json",
    "https://raw.githubusercontent.com/Whoahaow/rjsxrd/main/githubmirror/default/24.txt"
]

def harvest():
    final_nodes = []
    seen_uids = set() # 用来物理去重
    name_counts = {}  # 用来解决 Clash 同名覆盖问题
    headers = {'User-Agent': 'Mozilla/5.0'}

    for url in TARGET_URLS:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200: continue
            content = resp.text
            
            # 1. 专门对付 hysteria2:// 链接 (优先级最高，最准)
            links = re.findall(r"hysteria2://([^@]+)@([\w\d\.-]+?\.fastervpn\.world):(\d+)", content, re.I)
            for pwd, host, port in links:
                uid = f"{host}:{port}:{pwd}"
                if uid not in seen_uids:
                    # 解决同名问题
                    base_name = host
                    name_counts[base_name] = name_counts.get(base_name, 0) + 1
                    display_name = f"{base_name}_{name_counts[base_name]}"
                    
                    node = f"{{name: '{display_name}', server: {host}, port: {port}, type: hysteria2, password: '{pwd}', sni: {host}, skip-cert-verify: true}}"
                    final_nodes.append(node)
                    seen_uids.add(uid)

            # 2. 专门对付 YAML/JSON 块 (更加严谨的查找)
            # 这种格式通常密码在域名后面几行
            blocks = re.split(r'-\s+name:|{', content)
            for block in blocks:
                if "fastervpn.world" in block:
                    h_m = re.search(r"([\w\d\.-]+?\.fastervpn\.world)", block)
                    p_m = re.search(r"(?:port|server_port)[:\"\s]+(\d+)", block)
                    # 这里的正则加强了，排除掉引号和逗号
                    pw_m = re.search(r"(?:password|auth_str)[:\"\s]+['\"]?([^'\"\s,{}]+)['\"]?", block)
                    
                    if h_m and p_m:
                        host = h_m.group(1).lower()
                        port = p_m.group(1)
                        pwd = pw_m.group(1) if pw_m else "test.+"
                        uid = f"{host}:{port}:{pwd}"
                        if uid not in seen_uids:
                            base_name = host
                            name_counts[base_name] = name_counts.get(base_name, 0) + 1
                            display_name = f"{base_name}_{name_counts[base_name]}"
                            
                            node = f"{{name: '{display_name}', server: {host}, port: {port}, type: hysteria2, password: '{pwd}', sni: {host}, skip-cert-verify: true}}"
                            final_nodes.append(node)
                            seen_uids.add(uid)
        except: continue
            
    return final_nodes

if __name__ == "__main__":
    nodes = harvest()
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        for n in nodes: f.write(f"  - {n}\n")
    print(f"任务结束：共抓取 {len(nodes)} 个节点，已处理同名覆盖。")
