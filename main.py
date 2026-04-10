import requests
import re
import os

# 1. 依然瞄准你手动确认过的这些高质量“老巢”
TARGET_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt",
    "https://raw.githubusercontent.com/shaoyouvip/free/main/all.yaml",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/singbox.json",
    "https://raw.githubusercontent.com/Whoahaow/rjsxrd/main/githubmirror/default/24.txt"
]

def harvest():
    raw_text = ""
    for url in TARGET_URLS:
        try:
            print(f"[*] 正在突击仓库: {url}")
            # 增加 headers 模拟浏览器，防止被拦截
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                raw_text += resp.text + "\n"
                print(f"[OK] 成功获取内容，长度: {len(resp.text)}")
        except Exception as e:
            print(f"[Error] 访问失败: {url}, 原因: {e}")
            continue
    
    # 2. 暴力正则：只要包含 fastervpn.world 且紧跟数字端口
    # 匹配: vpn-xxx.fastervpn.world:443 或 "server": "vpn-xxx.fastervpn.world", "port": 443 等
    regex = r"([\w\d\.-]+?\.fastervpn\.world).*?[:\"'\s]+(\d{2,5})"
    matches = re.findall(regex, raw_text, re.IGNORECASE)
    
    final_nodes = []
    seen_ids = set()
    
    print(f"[*] 正则匹配完成，初步筛选出 {len(matches)} 个潜在节点")
    
    for server, port in matches:
        server = server.strip().lower()
        port = port.strip()
        uid = f"{server}:{port}"
        
        # 去重，但不再测速
        if uid not in seen_ids:
            # 统一转换成 Clash 格式
            node_yaml = (
                f"{{name: '{server}', server: {server}, port: {port}, "
                f"type: hysteria2, password: 'fastervpn.world', "
                f"up: 20, down: 80, sni: {server}, skip-cert-verify: true}}"
            )
            final_nodes.append(node_yaml)
            seen_ids.add(uid)
            
    return final_nodes

if __name__ == "__main__":
    print("--- 暴力收割模式启动（已关闭测速） ---")
    nodes = harvest()
    
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        if nodes:
            for n in nodes:
                f.write(f"  - {n}\n")
            print(f"--- 任务完成，成功导出 {len(nodes)} 个节点 ---")
        else:
            f.write("  # 奇怪，竟然一个都没捞到，请检查 TARGET
