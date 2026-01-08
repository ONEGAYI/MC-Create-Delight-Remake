import socket
import time
import sys

# ================= 配置区域 =================
# 将此处修改为你的服务器 IP
SERVER_IP = "103.83.72.165"  
SERVER_PORT = 11397          # 对应的测试端口
# ===========================================

def run_client():
    print(f"\n[CLIENT] 开始 UDP 连通性测试")
    print(f"[CLIENT] 目标: {SERVER_IP}:{SERVER_PORT}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)  # 设置2秒超时
    
    packets_to_send = 5
    packets_received = 0
    
    print("-" * 50)
    
    for i in range(1, packets_to_send + 1):
        message = f"PING_PACKET_{i}"
        send_data = message.encode('utf-8')
        
        try:
            start_time = time.time()
            # 发送数据
            sock.sendto(send_data, (SERVER_IP, SERVER_PORT))
            print(f"[发送 #{i}] 正在等待回复...", end="\r")
            
            # 接收回复
            data, addr = sock.recvfrom(1024)
            end_time = time.time()
            
            rtt = (end_time - start_time) * 1000
            print(f"[成功 #{i}] 收到回复: {data.decode()} | 延迟: {rtt:.2f}ms")
            packets_received += 1
            
        except socket.timeout:
            print(f"[超时 #{i}] 2秒内未收到服务器回复 (数据包丢失或被拦截)")
        except OSError as e:
            print(f"[错误 #{i}] 网络不可达: {e}")
        
        # 稍微停顿一下，避免发包太快
        time.sleep(0.5)

    print("-" * 50)
    
    # 结果分析
    loss_rate = ((packets_to_send - packets_received) / packets_to_send) * 100
    print(f"\n[测试结果]")
    print(f"发送: {packets_to_send}, 接收: {packets_received}")
    print(f"丢包率: {loss_rate}%")
    
    if packets_received == 0:
        print("\n[结论] ❌ UDP 完全不通")
        print("原因可能为：")
        print("1. 服务器防火墙没开 11397 端口 (请检查云控制台)")
        print("2. 客户端网络/运营商拦截了 UDP 流量 (请尝试加速器或手机热点)")
    elif packets_received < packets_to_send:
        print("\n[结论] ⚠️ 网络存在严重波动/丢包")
        print("UDP 通道是开的，但不稳定，会导致语音断断续续。")
    else:
        print("\n[结论] ✅ UDP 网络完美连通")
        print("如果脚本能通但游戏不通，说明问题出在 SimpleVoiceChat 的配置或端口 11396 被特定拦截。")

    sock.close()
    input("\n按回车键退出...")

if __name__ == "__main__":
    run_client()