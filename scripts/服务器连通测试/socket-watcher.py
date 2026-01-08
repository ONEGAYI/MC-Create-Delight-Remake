import socket
import sys

# 监听配置
BIND_IP = "0.0.0.0"  # 监听所有网卡
BIND_PORT = 11397    # 避开原本的 11396

def run_server():
    # 创建 UDP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        sock.bind((BIND_IP, BIND_PORT))
        print(f"\n[SERVER] UDP 监听服务已启动")
        print(f"[SERVER] 正在监听端口: {BIND_PORT}")
        print(f"[SERVER] 请确保云服务器防火墙已放行该端口的 UDP 流量！")
        print(f"[SERVER] 按 Ctrl+C 停止服务...\n")
        
        while True:
            # 接收数据
            try:
                data, addr = sock.recvfrom(1024)
                client_ip, client_port = addr
                
                content = data.decode('utf-8', errors='ignore')
                print(f"[收到请求] 来自: {client_ip}:{client_port} | 内容: {content}")
                
                # 发送回执 (Handshake Response)
                response = f"SERVER_ACK_FOR_{content}".encode('utf-8')
                sock.sendto(response, addr)
                print(f"[已回复] 发送 ACK 到 {client_ip}:{client_port}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[错误] {e}")
                
    except OSError as e:
        print(f"[启动失败] 端口可能被占用或权限不足: {e}")
    finally:
        sock.close()
        print("\n[SERVER] 服务已关闭")

if __name__ == "__main__":
    run_server()