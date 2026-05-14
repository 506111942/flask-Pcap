from scapy.all import *
import time

# ---------------------- 配置区 ----------------------
NUM_PACKETS = 10  # 生成10个数据包，时间序列就会有10个点
INTERVAL_SECONDS = 10  # 每个包之间间隔10秒
OUTPUT_FILE = "multi_time_test.pcap"  # 输出文件名
# ----------------------------------------------------

packets = []
base_time = time.time()  # 以当前时间为基准时间

for i in range(NUM_PACKETS):
    # 生成一个HTTP数据包
    pkt = IP(src="192.168.1.100", dst="8.8.8.8") / TCP(dport=80) / Raw(load=f"GET /test{i} HTTP/1.1")

    # 给每个包设置不同的时间戳（基准时间 + 间隔*i）
    pkt.time = base_time + (i * INTERVAL_SECONDS)

    packets.append(pkt)

# 保存为pcap文件
wrpcap(OUTPUT_FILE, packets)
print(f"✅ 成功生成 {OUTPUT_FILE}，包含 {len(packets)} 个数据包，时间间隔 {INTERVAL_SECONDS} 秒")