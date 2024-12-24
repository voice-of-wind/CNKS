import matplotlib
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

def plot_speed_vs_threads():
    threads = []
    speeds = []
    with open("speed.txt", "r", encoding="utf-8") as f:
        for line in f:
            try:
                speed, thread = line.strip().split(',')
                speeds.append(float(speed.split()[0]))
                threads.append(int(thread.split()[0]))
            except:
                continue

    plt.figure()
    plt.plot(threads, speeds, marker='o')
    plt.title('传输速度 vs 线程数量')
    plt.xlabel('线程数量')
    plt.ylabel('传输速度 (KB/s)')
    plt.grid(True)
    plt.savefig('speed_vs_threads.png')
    plt.show()

plot_speed_vs_threads()

