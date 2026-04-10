import requests
import re
import socket
import concurrent.futures
import os

TOKEN = os.environ.get("MY_GITHUB_TOKEN")

def check_tcp(server, port):
    try:
        with socket.create_connection((server, int(port)), timeout=2):
            return True
    except:
        return False

def search_github():
    if not TOKEN:
        print("[!] 错误: 未检测到 MY_GITHUB_TOKEN")
        return ""
    
    # 扩大搜索范围：尝试搜索所有包含 fastervpn.world 的文件
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
                raw_url = item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                try:
                    combined_content += requests.get(raw_url, timeout=5).text + "\n"
                except: continue
        else:
            print(f"[!] 搜索 API 响应异常: {resp.status_code}")
    except Exception as e:
        print(f"[!] 搜索出错: {e}")
    
    return combined_content

def extract_nodes(content):
    # 更加稳健的匹配：直接抓取整个 YAML 字典块
    blocks = re.findall(r"-\s*\{[^}]*?fastervpn\.world[^}]*?\}", content)
    
    final_nodes = []
    seen_ids = set()
    
    for block in blocks:
        try:
            # 改进正则，防止 group 提取失败
            s_match = re.search(r"server:\s*([^, \}\n\r]+)", block)
            p_match = re.search(r"port:\s*(\d+)", block)
            
            # 只有当 server 和 port 都存在时才处理
            if s_match and p_match:
                server = s_match.group(1).strip()
                port = p_match.group(1).strip() if p_match.groups() == 0 else p_match.group(1).strip()
                # 为了防止报错，统一使用 group(1) 匹配到的第一组
                port = p_match.group(1)
                
                unique_id = f"{server}:{port}"
                
                if unique_id not in seen_ids:
                    if check_tcp(server, port):
                        print(f"[+] 活节点捕获: {server}")
                        final_nodes.append(block)
                        seen_ids.add(unique_id)
        except Exception:
            # 遇到格式错乱的节点，直接跳过，不崩溃
            continue
            
    return final_nodes

if __name__ == "__main__":
    raw_data = search_github()
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
