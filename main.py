import requests
import re
import socket
import concurrent.futures
import base64
import os

# 1. 配置你的 Token (脚本会自动从 Github Action 环境中读取)
# 如果本地测试，可以手动填入 "ghp_xxxx"
TOKEN = os.environ.get("MY_GITHUB_TOKEN")

def check_tcp(server, port):
    try:
        with socket.create_connection((server, int(port)), timeout=2):
            return True
    except:
        return False

def search_github():
    if not TOKEN:
        print("[!] 错误: 未检测到 MY_GITHUB_TOKEN，搜索功能受限")
        return ""
    
    # 模仿你手动的搜索动作：搜索包含 fastervpn.world 的 yaml 或 json 文件
    url = "https://api.github.com/search/code?q=fastervpn.world+extension:yaml+extension:json"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    combined_content = ""
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            items = resp.json().get('items', [])
            print(f"[*] 全网搜索找到 {len(items)} 个相关文件，正在提取内容...")
            for item in items:
                # 转换成 Raw 链接直接下载
                raw_url = item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                try:
                    combined_content += requests.get(raw_url, timeout=5).text + "\n"
                except: continue
        else:
            print(f"[!] 搜索失败: {resp.status_code}, 可能是 Token 权限问题")
    except Exception as e:
        print(f"[!] 搜索出错: {e}")
    
    return combined_content

def extract_nodes(content):
    # 匹配所有的 Hysteria2 节点块
    blocks = re.findall(r"-\s*\{[^}]*?fastervpn\.world[^}]*?\}", content)
    
    final_nodes = []
    seen_ids = set()
    
    for block in blocks:
        s_match = re.search(r"server:\s*([^, \}\n\r]+)", block)
        p_match = re.search(r"port:\s*(\d+)", block)
        
        if s_match and p_match:
            server = s_match.group(1).strip()
            port = p_match.group(2).strip()
            unique_id = f"{server}:{port}"
            
            if unique_id not in seen_ids:
                if check_tcp(server, port):
                    print(f"[+] 活节点捕获: {server}")
                    final_nodes.append(block)
                    seen_ids.add(unique_id)
    return final_nodes

if __name__ == "__main__":
    # 第一步：全网搜索
    raw_data = search_github()
    # 第二步：测速并过滤
    live_nodes = extract_nodes(raw_data)
    
    print(f"\n[!] 任务完成，捕获活节点: {len(live_nodes)} 个")
    
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        if live_nodes:
            for node in live_nodes:
                line = node.strip().lstrip('-').strip()
                f.write(f"  - {line}\n")
        else:
            f.write("  # 本次搜索未发现可用活节点\n")
