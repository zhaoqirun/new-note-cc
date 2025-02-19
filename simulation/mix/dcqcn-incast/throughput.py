import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import os
# 定义文件路径
file_path = './output.txt'
print("Current working directory:", os.getcwd())

# 2000055540 n:338 4:3 100608 Enqu ecn:0 0b00d101 0b012301 10000 100 U 161000 0 3 1048(1000)`

# It means: at time 2000055540ns, at node 338, port 4, queue #3, the queue length is 100608B, and a packet is enqueued; 
# the packet does not have ECN marked, is from 11.0.209.1:10000 to 11.1.35.1:100, is a data packet (U), sequence number 161000, 
# tx timestamp 0, priority group 3, packet size 1048B, payload 1000B.
# # 解析每行数据的函数

# 2000000000 n:2 1:3 0 Dequ ecn:0 0b000201 0b000101 10000 100 U 0 0 3 1048(1000)
# 2000532540 n:16 3:0 0 Enqu ecn:0 0a011101 ffffffff P 5 0 3 43
def parse_line(line):
    parts = line.strip().split()
    # print(parts)
    if parts[7] == 'ffffffff':
        return None
    else:
        return {
        "time_ns": int(parts[0]),
        "node": int(parts[1].split(":")[1]),
        "send_or_not": parts[4],
        "packet_type": parts[10],
        "packet_size": int(parts[14].split("(")[0]),  # 提取包大小
        }

# 读取文件并解析每一行
with open(file_path, 'r') as f:
    lines = f.readlines()

# 将解析后的数据转为DataFrame

data = pd.DataFrame([parse_line(line) for line in lines if parse_line(line) is not None])


#  if line[7] != 'ffffffff'

# 将时间转换为微秒
data['time_us'] = data['time_ns'] // 1000

# filtered_data = data[(data['node'] <16) & (data['send_or_not'] != 'Dequ')]
# print(filtered_data)

# exit(0)


# 只保留数据包类型为 'U' 的行
filtered_data = data[(data['packet_type'] == 'U') & (data['send_or_not'] == 'Dequ') ] 
# filtered_data = data[(data['packet_type'] == 'U') & (data['send_or_not'] == 'Dequ')  & (data['time_ns'] <=2020000000)] 

# 


# 创建全局的时间区间范围
start_time = filtered_data['time_us'].min()
end_time = filtered_data['time_us'].max()
all_time_bins = range((start_time // 10), (end_time // 10) + 1, 1)

# 初始化字典来存储每个节点的吞吐量计算结果
throughput_results = defaultdict(list)

max_node = data['node'].max()
# 对每个节点计算吞吐量
for node in range(max_node  + 1):
    node_data = filtered_data[filtered_data['node'] == node]
    # 创建每 10 微秒的时间区间
    node_data['time_bin'] = (node_data['time_us'] // 10)     
    # 计算每个 10 微秒区间内的吞吐量
    throughput = node_data.groupby('time_bin')['packet_size'].sum() / 10  # 单位：字节/微秒   

    # 将结果对齐到完整的时间区间范围
    throughput_aligned = pd.Series(0, index=all_time_bins)  # 默认吞吐量为 0
    throughput_aligned.update(throughput)  # 更新有数据的时间区间
    
    # 保存为 (时间点, 吞吐量) 的列表
    throughput_results[node] = list(throughput_aligned.items())

    # throughput_results[node] = list(throughput.items())  # 保存为 (时间点, 吞吐量) 的列表
    

print(throughput_results)

# # 输出每个节点的吞吐量结果
# for node, values in throughput_results.items():
#     print(f"Node {node}:")
#     for time_bin, throughput in values:
#         print(f"Time {time_bin}us, Throughput: {throughput} bytes/us")

# 将吞吐量结果转换为 (时间, 吞吐量) 二维数组形式，并进行单位转换


node_throughputs = {node: [] for node in range(8)}

for node in range(8):
    for time_bin, throughput in throughput_results[node]:
        # time_bin 转为秒，throughput 转为 GB/s
        time_sec = time_bin / 1e5  # 从10微秒到秒
        throughput_gb = throughput / 1e3  # 从 B/μs 到 GB/s
        node_throughputs[node].append((time_sec, throughput_gb))

# 绘制图表
plt.figure(figsize=(60, 8))

for node in range(8):
    times, throughputs = zip(*node_throughputs[node])
    plt.plot(times, throughputs, label=f'Node {node}', linewidth=1)

# plt.xlabel('Time (seconds)')
# plt.ylabel('Throughput (GB/s)')
# plt.title('Throughput over Time for Nodes 0-7')
# plt.legend()
# plt.grid(True)
# plt.show()
# 设置标题和轴标签
plt.title('Throughput Over Time for Nodes 0-7', fontsize=20, fontweight='bold', pad=20)
plt.xlabel('Time (seconds)', fontsize=14, labelpad=15)
plt.ylabel('Throughput (GB/s)', fontsize=14, labelpad=15)

# 添加网格线
plt.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.7)  # 使用虚线和较浅的颜色增强背景

# 调整刻度字体
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.savefig('throughput_plot_all_s.png')  # 保存为 PNG 格式
plt.show()
