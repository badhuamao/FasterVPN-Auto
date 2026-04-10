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
    seen = set()
    headers = {'User-Agent': 'Mozilla/5.0'}

    for url in TARGET_URLS:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200: continue
            
            content = resp.text
            # 1. 尝试匹配 hysteria2:// 格式 (包含密码)
            # 格式通常是: hysteria2://password@host:port?...
            link_regex = r"hysteria2://([^@]+)@([\w\d\.-]+?\.fastervpn\.world):(\d+)"
            for pwd, host, port in re.findall(link_regex, content, re.I):
                uid = f"{host.lower()}:{port}"
                if uid not in seen:
                    node = f"{{name: '{host}', server: {host}, port: {port}, type: hysteria2, password: '{pwd}', sni: {host}, skip-cert-verify: true}}"
                    final_nodes.append(node)
                    seen.add(uid)

            # 2. 尝试匹配 YAML/JSON 里的 password 字段
            # 我们找那些域名和密码离得很近的行
            blocks = re.split(r'-\s+name:|{', content)
            for block in blocks:
                if "fastervpn.world" in block:
                    host_m = re.search(r"([\w\d\.-]+?\.fastervpn\.world)", block)
                    port_m = re.search(r"(?:port|server_port)[:\"\s]+(\d+)", block)
                    pwd_m = re.search(r"(?:password|auth_str)[:\"\s]+['\"]?([^'\"\s,{}]+)['\"]?", block)
                    
                    if host_m and port_m:
                        host = host_m.group(1).lower()
                        port = port_m.group(1)
                        pwd = pwd_m.group(1) if pwd_m else "test.+" # 找不到就用你截图中出现的默认密码
                        uid = f"{host}:{port}"
                        if uid not in seen:
                            node = f"{{name: '{host}', server: {host}, port: {port}, type: hysteria2, password: '{pwd}', sni: {host}, skip-cert-verify: true}}"
                            final_nodes.append(node)
                            seen.add(uid)
        except: continue
            
    return final_nodes

if __name__ == "__main__":
    nodes = harvest()
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        if nodes:
            for n in nodes: f.write(f"  - {n}\n")
        else:
            f.write("  # No nodes found\n")
    print(f"Done. Found {len(nodes)} nodes.")
