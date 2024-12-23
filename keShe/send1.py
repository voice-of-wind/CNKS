import socket
import os
import tkinter as tk
from tkinter import filedialog, ttk
import hashlib
import time
import threading
from PIL import Image, ImageTk  
THREADS = 6
# 规定一个标识符用来区分发送文件的开头
beginImgF = b"#####*****img#####*****"
beginAudioF = b"#####*****audio#####*****"
beginVideoF = b"#####*****video#####*****"
beginF = b"#####*****file#####*****"
beginOfficeF = b"#####*****office#####*****"
beginZipF = b"#####*****zip#####*****"
# 发送文件名和文件类型开始符后的分隔符
splitF = b"#####-----#####"
endF = b"#####*****end_of_file*****#####"
allEnd = b"#####*****all_end*****#####"
fileTypes = ["img", "audio", "video", "file", "office", "zip"]

# 根据文件后缀确定文件类型从而发送对应标识符
def get_file_type(file_path):
    file_name, file_extension = os.path.splitext(file_path)
    if file_extension in ['.png', '.jpg', '.jpeg', '.gif']:
        return beginImgF
    elif file_extension in ['.mp3', '.wav', '.flac']:
        return beginAudioF
    elif file_extension in ['.mp4', '.avi', '.mov']:
        return beginVideoF
    elif file_extension in ['.txt']:
        return beginF
    elif file_extension in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
        return beginOfficeF
    elif file_extension in ['.zip', '.rar', '.7z']:
        return beginZipF
    else:
        return -1

def send_file_tcp(file_paths, host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        buffer_size = 1024*8 *2# 缓冲区大小
        # 遍历文件列表 依次发送文件
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            # 发送文件标识符
            typeF = get_file_type(file_path)
            buffer = typeF + splitF + file_name.encode('utf-8') + splitF + str(file_size).encode('utf-8') + splitF
            s.sendall(buffer)
            # 发送文件内容

            sent_size = 0
            start_time = time.time()
            speed = 0
            with open(file_path, 'rb') as f:
                while (chunk := f.read(buffer_size)):
                    s.sendall(chunk)
                    sent_size += len(chunk)
                    progress = (sent_size / file_size) * 100
                    progress_var.set(progress)

                    elapsed_time = time.time() - start_time

                    if elapsed_time > 0:
                        speed = sent_size / elapsed_time / 1024  # KB/s
                    speed_label.config(text=f"传输速率: {speed:.2f} KB/s")
                    root.update_idletasks()
            # 发送文件结束标识符
            s.sendall(endF)

            print(f"{file_name} 文件发送完成")

def send_file_udp(file_paths, host, port):
    buffer_size1 = 1024*4*8  # 缓冲区大小
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:

        # 遍历文件列表 依次发送文件
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            sent_size = 0
            nowIndex = 0
            # 发送文件标识符和文件名
            typeF = get_file_type(file_path)
            buffer = typeF + splitF + file_name.encode('utf-8') + splitF + str(file_size).encode('utf-8') + splitF

            # 发送文件内容
            start_time = time.time()
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(buffer_size1 - len(buffer)-32)
                    if not chunk:
                        break
                    buffer += chunk
                    # +str(nowIndex).encode('utf-8')
                    checksum = hashlib.md5(buffer+str(nowIndex).encode('utf-8')).hexdigest().encode('utf-8')
                    buffer += checksum
                    speed = 0
                    while True:
                        s.sendto(buffer, (host, port))

                        ack,_ = s.recvfrom(buffer_size1)
                        if b'ACK' == ack:
                            nowIndex+=1
                            break
                        else:
                            print(f"重传数据包1 当前块数{nowIndex}")

                    
                    sent_size += len(buffer)-32
                    progress = (sent_size / file_size) * 100
                    progress_var.set(progress)
                    elapsed_time = time.time() - start_time

                    if elapsed_time>0:
                        speed = sent_size / elapsed_time / 1024  # KB/s
                    speed_label.config(text=f"传输速率: {speed:.2f} KB/s")
                    root.update_idletasks()
                    buffer = b''

            # 发送文件结束标识符
            while True:
                checksum = hashlib.md5(endF+str(nowIndex).encode('utf-8')).hexdigest().encode('utf-8')
                s.sendto(endF+checksum, (host, port))
                ack, _ = s.recvfrom(buffer_size1)
                if ack == b'ACK':
                    print(f"{file_name} 文件发送完成")
                    break
        #发送所有文件完成标识符
        while True:
            checksum = hashlib.md5(allEnd+"0".encode('utf-8')).hexdigest().encode('utf-8')
            s.sendto(allEnd + checksum, (host, port))
            ack, _ = s.recvfrom(buffer_size1)
            if ack == b'ACK':
                print(f"{file_name} 文件发送完成")
                break




    print("本次所有文件发送完成")


# 定义一个函数指定文件的起始 结束部分
is_oky = 0
flag_lock = threading.Lock()
def set_is_oky(value):
    global is_oky
    with flag_lock:
        if value == 1:
            is_oky += 1
        elif value == 0:
            is_oky = 0

# 发送文件分块的函数
def send_chunk(file_path, host, port, start, end, thread_num, file_id,file_size):
    buffer_size = 4 * 1024 * 16 # 设置缓冲区大小
    global is_oky
    global sent_size, start_time
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))

        with open(file_path, 'rb') as f:
            f.seek(start)
            while start < end:
                headers = f"{file_id}:{end}:{start}:{file_size}".encode('utf-8')
                chunk_size = min(buffer_size-len(headers)-len(b'::'), end - start)  # 计算每次发送的块大小
                chunk = f.read(chunk_size)
                # 发送数据块标识符和数据块
                data = headers + b"::" + chunk
                s.sendall(data)
                start += chunk_size
                # 更新进度和速率显示
                sent_size += len(chunk)
                progress = (sent_size / file_size) * 100
                progress_var.set(progress)
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    speed = sent_size / elapsed_time / 1024  # KB/s
                speed_label.config(text=f"传输速率: {speed:.2f} KB/s")
                progress_label.config(text=f"{progress:.2f}%")
                root.update_idletasks()


        print("发送完成")
        ack = s.recv(1024)
        if ack == b"ACK":
            set_is_oky(1)

        while is_oky < thread_num:
            pass
        print(f"文件{file_id}发送完成")




def send_chunk_end(host,port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(b"###AllEnd###")


# 发送端主函数
def send_file_tcp_multithread(file_paths, host, port, num_threads=THREADS):
    global sent_size, start_time
    for index in range(len(file_paths)+1):
        if index == len(file_paths):
            # 所有文件发送完毕 再最后建立几个子进程连接用来发送结束标识符
            threads = []
            for i in range(num_threads):
                thread = threading.Thread(target=send_chunk_end,args=(host,port))
                thread.start()
                threads.append(thread)
                # 等待所有线程完成文件传输
            for thread in threads:
                thread.join()

            print("本次所有文件发送完成")
        else:
            file_path = file_paths[index]
            file_size = os.path.getsize(file_path)
            chunk_size = file_size // num_threads
            threads = []
            file_id = os.path.basename(file_path)  # 使用文件名作为文件唯一标识符
            print(f"开始发送文件 {file_id}  文件大小 {file_size}")
            sent_size = 0
            start_time = time.time()
            
            for i in range(num_threads):
                start = i * chunk_size
                end = file_size if i == num_threads - 1 else (i + 1) * chunk_size
                print(f"分配数据块 {start} 到 {end}")
                thread = threading.Thread(target=send_chunk, args=(file_path, host, port, start, end, num_threads, file_id,file_size))
                threads.append(thread)
                thread.start()

            # 等待所有线程完成文件传输
            for thread in threads:
                thread.join()

            sent_size = 0
            set_is_oky(0)





def select_files():
    file_paths = filedialog.askopenfilenames()
    if file_paths:
        for file_path in file_paths:
            listbox_files.insert(tk.END, file_path)

def send_files():
    file_paths = listbox_files.get(0, tk.END)
    host = entry_host.get()
    port = int(entry_port.get())
    protocol = protocol_var.get()
    if protocol == "TCP":
        send_file_tcp(file_paths, host, port)
    elif protocol == "UDP":
        send_file_udp(file_paths, host, port)
    elif protocol == "TCP_multiThread":
        num_threads = int(entry_threads.get())
        # send_file_tcp_multithread(file_paths, host, port, num_threads)
        #创建一个线程用来发送文件
        thread = threading.Thread(target=send_file_tcp_multithread, args=(file_paths, host, port, num_threads))
        thread.start()
    # 发送完成后清空文件列表
    listbox_files.delete(0, tk.END)

# 创建主窗口
root = tk.Tk()
root.title("文件发送器")

# 文件路径输入框和按钮
frame_file = tk.Frame(root)
frame_file.pack(pady=10)
label_file_path = tk.Label(frame_file, text="文件路径:")
label_file_path.pack(side=tk.LEFT)
button_browse = tk.Button(frame_file, text="浏览", command=select_files)
button_browse.pack(side=tk.LEFT)

# 文件列表框
frame_files = tk.Frame(root)
frame_files.pack(pady=10)
label_files = tk.Label(frame_files, text="选中的文件:")
label_files.pack()
listbox_files = tk.Listbox(frame_files, width=50, height=10)
listbox_files.pack()

# 第一行：主机地址、端口号
frame_host_port = tk.Frame(root)
frame_host_port.pack(pady=10)

label_host = tk.Label(frame_host_port, text="主机地址:")
label_host.pack(side=tk.LEFT)
entry_host = tk.Entry(frame_host_port, width=20)
entry_host.pack(side=tk.LEFT, padx=5)
entry_host.insert(0, "127.0.0.1")  # 设置默认值

label_port = tk.Label(frame_host_port, text="端口号:")
label_port.pack(side=tk.LEFT)
entry_port = tk.Entry(frame_host_port, width=10)
entry_port.pack(side=tk.LEFT, padx=5)
entry_port.insert(0, "12345")  # 设置默认值

# 第二行：选择协议、发送按钮
frame_protocol_send = tk.Frame(root)
frame_protocol_send.pack(pady=10)

label_protocol = tk.Label(frame_protocol_send, text="选择协议:")
label_protocol.pack(side=tk.LEFT)
protocol_var = tk.StringVar(value="UDP")
protocol_menu = ttk.Combobox(frame_protocol_send, textvariable=protocol_var, values=["TCP", "UDP", "TCP_multiThread"], state="readonly")
protocol_menu.pack(side=tk.LEFT, padx=5)

button_send = tk.Button(frame_protocol_send, text="发送", command=send_files)
button_send.pack(side=tk.LEFT, padx=5)

# 进度条、传输速率标签放在一行
frame_progress = tk.Frame(root)
frame_progress.pack(pady=10)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame_progress, variable=progress_var, maximum=100)
progress_bar.pack(side=tk.LEFT, padx=5)

progress_label = tk.Label(frame_progress, text="0%")
progress_label.pack(side=tk.LEFT, padx=5)

speed_label = tk.Label(frame_progress, text="传输速率: 0 KB/s")
speed_label.pack(side=tk.LEFT, padx=5)

# 线程数量输入框
frame_threads = tk.Frame(root)
frame_threads.pack(pady=10)
label_threads = tk.Label(frame_threads, text="线程数量:")
label_threads.pack(side=tk.LEFT)
entry_threads = tk.Entry(frame_threads, width=10)
entry_threads.pack(side=tk.LEFT, padx=5)
entry_threads.insert(0, str(THREADS))  # 设置默认值



# 运行主循环
root.mainloop()