import socket
import os
import tkinter as tk
from tkinter import filedialog, ttk
import hashlib
import time
import threading

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

fileTypes = ["img", "audio", "video", "file", "office", "zip"]

class FileSender:
    def __init__(self, root):
        self.root = root
        self.root.title("文件发送器")

        # 文件路径输入框和按钮
        frame_file = tk.Frame(root)
        frame_file.pack(pady=10)
        label_file_path = tk.Label(frame_file, text="文件路径:")
        label_file_path.pack(side=tk.LEFT)
        button_browse = tk.Button(frame_file, text="浏览", command=self.select_files)
        button_browse.pack(side=tk.LEFT)

        # 文件列表框
        frame_files = tk.Frame(root)
        frame_files.pack(pady=10)
        label_files = tk.Label(frame_files, text="选中的文件:")
        label_files.pack()
        self.listbox_files = tk.Listbox(frame_files, width=50, height=10)
        self.listbox_files.pack()

        # 主机地址输入框
        frame_host = tk.Frame(root)
        frame_host.pack(pady=10)
        label_host = tk.Label(frame_host, text="主机地址:")
        label_host.pack(side=tk.LEFT)
        self.entry_host = tk.Entry(frame_host, width=20)
        self.entry_host.pack(side=tk.LEFT, padx=5)
        self.entry_host.insert(0, "127.0.0.1")  # 设置默认值

        # 端口号输入框
        frame_port = tk.Frame(root)
        frame_port.pack(pady=10)
        label_port = tk.Label(frame_port, text="端口号:")
        label_port.pack(side=tk.LEFT)
        self.entry_port = tk.Entry(frame_port, width=10)
        self.entry_port.pack(side=tk.LEFT, padx=5)
        self.entry_port.insert(0, "12000")  # 设置默认值

        # 协议选择下拉菜单
        frame_protocol = tk.Frame(root)
        frame_protocol.pack(pady=10)
        label_protocol = tk.Label(frame_protocol, text="选择协议:")
        label_protocol.pack(side=tk.LEFT)
        self.protocol_var = tk.StringVar(value="UDP")
        self.protocol_menu = ttk.Combobox(frame_protocol, textvariable=self.protocol_var, values=["TCP", "UDP"],
                                          state="readonly")
        self.protocol_menu.pack(side=tk.LEFT, padx=5)

        # 发送按钮
        button_send = tk.Button(root, text="发送", command=self.send_files)
        button_send.pack(pady=20)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=10)

        # 传输速率标签
        self.speed_label = tk.Label(root, text="传输速率: 0 KB/s")
        self.speed_label.pack(pady=10)

    def select_files(self):
        file_paths = filedialog.askopenfilenames()
        if file_paths:
            for file_path in file_paths:
                self.listbox_files.insert(tk.END, file_path)

    def send_files(self):
        file_paths = self.listbox_files.get(0, tk.END)
        host = self.entry_host.get()
        port = int(self.entry_port.get())
        protocol = self.protocol_var.get()
        if protocol == "TCP":
            threading.Thread(target=self.send_file_tcp, args=(file_paths, host, port)).start()
        elif protocol == "UDP":
            threading.Thread(target=self.send_file_udp, args=(file_paths, host, port)).start()
        # 发送完成后清空文件列表
        self.listbox_files.delete(0, tk.END)

    def get_file_type(self, file_path):
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

    def send_file_tcp(self, file_paths, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))

            # 遍历文件列表 依次发送文件
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                # 发送文件标识符、文件长度和文件名
                typeF = self.get_file_type(file_path)
                buffer = typeF + splitF + str(file_size).encode('utf-8') + splitF + file_name.encode('utf-8') + splitF
                s.sendall(buffer)

                # 发送文件内容
                sent_size = 0
                start_time = time.time()
                with open(file_path, 'rb') as f:
                    while (chunk := f.read(1024)):
                        s.sendall(chunk)
                        sent_size += len(chunk)
                        progress = (sent_size / file_size) * 100
                        self.progress_var.set(progress)
                        self.progress_label.config(text=f"{progress:.2f}%")
                        elapsed_time = time.time() - start_time
                        speed = sent_size / elapsed_time / 1024  # KB/s
                        self.speed_label.config(text=f"传输速率: {speed:.2f} KB/s")
                        self.root.update_idletasks()
                # 发送文件结束标识符
                s.sendall(endF)

                print(f"{file_name} 文件发送完成")

    def send_file_udp(self, file_paths, host, port):
        buffer_size = 1024 * 8  # 缓冲区大小
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 遍历文件列表 依次发送文件
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                sent_size = 0

                # 发送文件标识符和文件名
                typeF = self.get_file_type(file_path)
                buffer = typeF + splitF + file_name.encode('utf-8') + splitF + str(file_size).encode('utf-8') + splitF

                # 发送文件内容
                start_time = time.time()
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(buffer_size - len(buffer) - 32)
                        if not chunk:
                            break
                        buffer += chunk
                        checksum = hashlib.md5(buffer).hexdigest().encode('utf-8')
                        buffer += checksum

                        while True:
                            s.sendto(buffer, (host, port))
                            try:
                                ack, _ = s.recvfrom(buffer_size)
                                if ack == b'ACK':
                                    break
                            except socket.timeout:
                                print("重传数据包")

                        sent_size += len(buffer) - 32
                        progress = (sent_size / file_size) * 100
                        self.progress_var.set(progress)
                        self.progress_label.config(text=f"{progress:.2f}%")
                        elapsed_time = time.time() - start_time
                        speed = sent_size / elapsed_time / 1024  # KB/s
                        self.speed_label.config(text=f"传输速率: {speed:.2f} KB/s")
                        self.root.update_idletasks()
                        buffer = b''
                    # 发送剩余的内容
                    if buffer:
                        checksum = hashlib.md5(buffer).hexdigest().encode('utf-8')
                        buffer += checksum
                        s.sendto(buffer, (host, port))
                        ack, _ = s.recvfrom(buffer_size)
                        if ack != b'ACK':
                            print("重传数据包")
                            s.sendto(buffer, (host, port))
                # 发送文件结束标识符
                checksum = hashlib.md5(endF).hexdigest().encode('utf-8')
                s.sendto(endF + checksum, (host, port))

                print(f"{file_name} 文件发送完成")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileSender(root)
    root.mainloop()