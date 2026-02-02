import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 示例数据：文件访问历史
data = {
    "path": [
        "file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt",
        "file6.txt", "file7.txt", "file8.txt", "file9.txt", "file10.txt"
    ],
    "access_time": [
        "2023-10-01 08:15:30",
        "2023-10-01 09:45:10",
        "2023-10-01 10:30:45",
        "2023-10-01 08:50:20",
        "2023-10-01 09:30:00",
        "2023-10-01 14:00:00",
        "2023-10-01 14:30:00",
        "2023-10-01 15:00:00",
        "2023-10-01 08:10:00",
        "2023-10-01 09:20:00",
    ]
}

# 将数据转换为 DataFrame
df = pd.DataFrame(data)

# 将访问时间转换为 datetime 类型
df["access_time"] = pd.to_datetime(df["access_time"])

# 提取小时信息
df["hour"] = df["access_time"].dt.hour

print(df["hour"])

# 统计每小时的访问次数
hourly_access = df["hour"].value_counts().sort_index()

print(hourly_access)

# 补全 24 小时的数据，缺失的小时补 0
full_hourly_access = hourly_access.reindex(range(24), fill_value=0)

print(f'full_hourly_access type{type(full_hourly_access)}')

# 计算平均值和标准差
mean_access = full_hourly_access.mean()
std_access = full_hourly_access.std()

print(f"每小时平均访问次数: {mean_access:.2f}")
print(f"每小时访问次数的标准差: {std_access:.2f}")

# 判断访问是否集中
if std_access > mean_access * 0.5:  # 标准差大于平均值的一半，认为是集中访问
    print("访问是集中式的。")
    # 找出访问次数最多的几个小时
    top_hours = full_hourly_access.nlargest(3)  # 找出访问次数最多的 3 个小时
    print("访问集中在以下小时：")
    for hour, count in top_hours.items():
        print(f"小时: {hour}, 访问次数: {count}")
else:
    print("访问是平均分散的。")

# 可视化每小时访问次数
plt.figure(figsize=(12, 6))
plt.bar(full_hourly_access.index, full_hourly_access.values, color='blue', alpha=0.7)
plt.axhline(mean_access, color='red', linestyle='dashed', linewidth=1, label=f'avg access count: {mean_access:.2f}')
plt.xlabel('Hour')
plt.ylabel('access count')
plt.title('Distribution')
plt.xticks(range(24))  # 确保 x 轴显示所有 24 个小时
plt.legend()
plt.show()