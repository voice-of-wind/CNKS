import matplotlib
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

def plot_speed_vs_threads():
    threads = []
    speeds = []
    with open("speed.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            speed_part, thread_part = line.split(",")
            speed_val = float(speed_part.replace("KB/s", "").strip())
            thread_val = int(thread_part.replace("threads", "").strip())
            speeds.append(speed_val)
            threads.append(thread_val)

    plt.figure()
    plt.plot(threads, speeds, marker='o')
    plt.title("线程数与传输速率折线图")
    plt.xlabel("线程数")
    plt.ylabel("传输速率 (KB/s)")
    plt.grid(True)
    plt.show()

plot_speed_vs_threads()

