import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 假设数据是一个包含文件路径和访问时间的DataFrame
data = {
    'path': ['file1', 'file2', 'file3', 'file4', 'file5', 'file6', 'file7'],
    'access_time': [
        '2023-10-01 14:30:00', '2023-10-02 09:15:00', '2023-10-03 14:45:00',
        '2023-10-04 14:20:00', '2023-10-05 10:00:00', '2023-10-06 14:10:00',
        '2023-10-07 14:50:00'
    ]
}

# 创建DataFrame
df = pd.DataFrame(data)

# 将access_time转换为datetime类型
df['access_time'] = pd.to_datetime(df['access_time'])

# 提取小时信息
df['hour'] = df['access_time'].dt.hour

# 统计每小时的访问频数
hourly_counts = df['hour'].value_counts().sort_index()

# 计算均值和标准差
mean_count = hourly_counts.mean()
std_count = hourly_counts.std()

print(f"每小时访问频数的均值: {mean_count}")
print(f"每小时访问频数的标准差: {std_count}")

# 判断是否集中分布
if std_count < mean_count:
    print("文件的访问集中在某些小时。")
else:
    print("文件的访问分布较为随机。")

# 可视化每小时的访问频数
plt.figure(figsize=(10, 6))
hourly_counts.plot(kind='bar', color='skyblue')
plt.title('File Access Frequency by Hour')
plt.xlabel('Hour of the Day')
plt.ylabel('Access Count')
plt.xticks(range(24), [f'{i}:00' for i in range(24)], rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()