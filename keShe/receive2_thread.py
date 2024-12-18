import socket
import os
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import uuid
import hashlib
import threading
import time


# region规定一个标识符用来区分发送文件的开头
beginImgF = b"#####*****img#####*****"
beginAudioF = b"#####*****audio#####*****"
beginVideoF = b"#####*****video#####*****"
beginF = b"#####*****file#####*****"
beginOfficeF = b"#####*****office#####*****"
beginZipF = b"#####*****zip#####*****"

splitF = b"#####-----#####"
endF = b"#####*****end_of_file*****#####"
fileTypes = ["img", "audio", "video", "file", "office", "zip"]
beginFs = [beginImgF, beginAudioF, beginVideoF, beginF, beginOfficeF, beginZipF]
#endregion

class FileReceiver:
    def __init__(self, root):
        self.root = root
        self.root.title("文件接收器")

        # 文件路径输入框和按钮
        frame_host_receive = tk.Frame(root)
        frame_host_receive.pack(pady=10)
        label_host_receive = tk.Label(frame_host_receive, text="主机地址:")
        label_host_receive.pack(side=tk.LEFT)
        self.entry_host_receive = tk.Entry(frame_host_receive, width=20)
        self.entry_host_receive.pack(side=tk.LEFT, padx=5)
        self.entry_host_receive.insert(0, "127.0.0.1")

        frame_port_receive = tk.Frame(root)
        frame_port_receive.pack(pady=10)
        label_port_receive = tk.Label(frame_port_receive, text="端口号:")
        label_port_receive.pack(side=tk.LEFT)
        self.entry_port_receive = tk.Entry(frame_port_receive, width=10)
        self.entry_port_receive.pack(side=tk.LEFT, padx=5)
        self.entry_port_receive.insert(0, "12000")

        frame_protocol = tk.Frame(root)
        frame_protocol.pack(pady=10)
        label_protocol = tk.Label(frame_protocol, text="选择协议:")
        label_protocol.pack(side=tk.LEFT)
        self.protocol_var = tk.StringVar(value="UDP")
        self.protocol_menu = ttk.Combobox(frame_protocol, textvariable=self.protocol_var, values=["TCP", "UDP"], state="readonly")
        self.protocol_menu.pack(side=tk.LEFT, padx=5)

        button_receive = tk.Button(root, text="开始接收", command=self.start_receiving)
        button_receive.pack(pady=20)

        frame_received_files = tk.Frame(root)
        frame_received_files.pack(pady=10)
        label_received_files = tk.Label(frame_received_files, text="接收到的文件:")
        label_received_files.pack()
        self.listbox_received_files = tk.Listbox(frame_received_files, width=50, height=10)
        self.listbox_received_files.pack()

        frame_file_display = tk.Frame(root)
        frame_file_display.pack(pady=10)
        label_file_display = tk.Label(frame_file_display, text="文件显示:")
        label_file_display.pack()
        self.listbox_file_display = tk.Listbox(frame_file_display, width=50, height=10)
        self.listbox_file_display.pack()

        frame_buttons = tk.Frame(root)
        frame_buttons.pack(pady=10)
        button_show_all = tk.Button(frame_buttons, text="所有文件", command=lambda: self.show_files(self.listbox_received_files.get(0, tk.END)))
        button_show_all.pack(side=tk.LEFT, padx=5)
        button_show_img = tk.Button(frame_buttons, text="图片文件", command=lambda: self.show_files(self.img_files))
        button_show_img.pack(side=tk.LEFT, padx=5)
        button_show_audio = tk.Button(frame_buttons, text="音频文件", command=lambda: self.show_files(self.audio_files))
        button_show_audio.pack(side=tk.LEFT, padx=5)
        button_show_video = tk.Button(frame_buttons, text="视频文件", command=lambda: self.show_files(self.video_files))
        button_show_video.pack(side=tk.LEFT, padx=5)
        button_show_office = tk.Button(frame_buttons, text="办公文件", command=lambda: self.show_files(self.office_files))
        button_show_office.pack(side=tk.LEFT, padx=5)
        button_show_text = tk.Button(frame_buttons, text="文本文件", command=lambda: self.show_files(self.text_files))
        button_show_text.pack(side=tk.LEFT, padx=5)
        button_show_zip = tk.Button(frame_buttons, text="压缩文件", command=lambda: self.show_files(self.zip_files))
        button_show_zip.pack(side=tk.LEFT, padx=5)

        button_download = tk.Button(root, text="下载选中文件", command=self.download_file)
        button_download.pack(pady=20)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=10)

        # 进度百分比标签
        self.progress_label = tk.Label(root, text="0%")
        self.progress_label.pack(pady=10)

        # 接收速率标签
        self.speed_label = tk.Label(root, text="接收速率: 0 KB/s")
        self.speed_label.pack(pady=10)

        # 全局变量
        self.file_paths = {}
        self.img_files = []
        self.audio_files = []
        self.video_files = []
        self.office_files = []
        self.text_files = []
        self.zip_files = []

    def get_file_type(self, data):
        if beginImgF in data:
            return 0
        elif beginAudioF in data:
            return 1
        elif beginVideoF in data:
            return 2
        elif beginF in data:
            return 3
        elif beginOfficeF in data:
            return 4
        elif beginZipF in data:
            return 5
        else:
            return -1

    def get_file_type_str(self, file_path):
        file_name, file_extension = os.path.splitext(file_path)
        if file_extension in ['.png', '.jpg', '.jpeg', '.gif']:
            return 0
        elif file_extension in ['.mp3', '.wav', '.flac']:
            return 1
        elif file_extension in ['.mp4', '.avi', '.mov']:
            return 2
        elif file_extension in ['.txt']:
            return 3
        elif file_extension in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
            return 4
        elif file_extension in ['.zip', '.rar', '.7z']:
            return 5
        else:
            return -1

    def receive_file_tcp(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            print("等待连接...")
            conn, addr = s.accept()
            print(f"连接来自: {addr}")
            save_paths = []
            file_names = []
            vaildData = ""
            isFirst = True
            remainData = False
            with conn:
                while True:
                    if not remainData:
                        data = conn.recv(1024)
                        remainData = False
                        fileType = self.get_file_type(data)
                        print(f"当前文件类型: {fileType}")
                        if not data:
                            break

                    if fileType != -1:
                        vaildData = data.split(beginFs[fileType])[1]
                        datas = vaildData.split(splitF, 3)
                        file_size = int(datas[2].decode('utf-8'))
                        file_name = datas[3].decode('utf-8')
                        print(f"当前接收文件: {file_name}")
                        unique_id = uuid.uuid4()
                        file_name = str(unique_id) + "-" + file_name
                        save_path = os.path.join(f"../receive/{fileTypes[fileType]}", file_name)
                        fileData = datas[3]
                        dir_path = os.path.dirname(save_path)
                        if not os.path.exists(dir_path):
                            print("创建目录")
                            os.makedirs(dir_path)
                        fileType = -1
                        received_size = 0
                        start_time = time.time()
                        with open(save_path, 'wb') as f:
                            f.write(fileData)
                            received_size += len(fileData)
                            while True:
                                chunk = conn.recv(1024)
                                if endF in chunk:
                                    print(f"最后一段数据: {chunk}")
                                    break
                                else:
                                    f.write(chunk)
                                    received_size += len(chunk)
                                    progress = (received_size / file_size) * 100
                                    self.progress_var.set(progress)
                                    self.progress_label.config(text=f"{progress:.2f}%")
                                    elapsed_time = time.time() - start_time
                                    speed = received_size / elapsed_time / 1024  # KB/s
                                    self.speed_label.config(text=f"接收速率: {speed:.2f} KB/s")
                                    self.root.update_idletasks()
                        save_paths.append(save_path)
                        file_names.append(file_name)
                        print(f"{file_name} 文件接收完成")
                    else:
                        break
        print("接收完成")
        return save_paths, file_names

    def receive_file_udp(self, host, port):
        udpRecSize = int(1024)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((host, port))
            print("等待连接...")
            save_paths = []
            file_names = []

            while True:
                data, addr = s.recvfrom(udpRecSize)
                if not data:
                    break
                fileType = self.get_file_type(data)
                print(f"当前文件类型: {fileType}")
                if fileType != -1:
                    vaildData = data.split(beginFs[fileType])[1]
                    datas = vaildData.split(splitF, 3)
                    file_size = int(datas[2].decode('utf-8'))
                    file_name = datas[3].decode('utf-8')
                    print(f"当前接收文件: {file_name}")
                    unique_id = uuid.uuid4()
                    file_name = str(unique_id) + "-" + file_name
                    save_path = os.path.join(f"../receive/{fileTypes[fileType]}", file_name)
                    fileData = datas[3]
                    dir_path = os.path.dirname(save_path)
                    if not os.path.exists(dir_path):
                        print("创建目录")
                        os.makedirs(dir_path)
                    fileType = -1
                    received_size = 0
                    start_time = time.time()
                    with open(save_path, 'wb') as f:
                        f.write(fileData)
                        received_size += len(fileData)
                        while True:
                            chunk, addr = s.recvfrom(udpRecSize)
                            if endF in chunk:
                                print(f"最后一段数据: {chunk}")
                                break
                            else:
                                data, checksum = chunk[:-32], chunk[-32:]
                                if hashlib.md5(data).hexdigest().encode('utf-8') == checksum:
                                    s.sendto(b'ACK', addr)
                                    f.write(data)
                                    received_size += len(data)
                                    progress = (received_size / file_size) * 100
                                    self.progress_var.set(progress)
                                    self.progress_label.config(text=f"{progress:.2f}%")
                                    elapsed_time = time.time() - start_time
                                    speed = received_size / elapsed_time / 1024  # KB/s
                                    self.speed_label.config(text=f"接收速率: {speed:.2f} KB/s")
                                    self.root.update_idletasks()
                                else:
                                    print("校验和错误，丢弃数据包")
                                    s.sendto(b'NACK', addr)
                    save_paths.append(save_path)
                    file_names.append(file_name)
                    print(f"{file_name} 文件接收完成")
                else:
                    print("未识别的文件类型")
        print("接收完成")
        return save_paths, file_names

    def start_receiving(self):
        host = self.entry_host_receive.get()
        port = int(self.entry_port_receive.get())
        protocol = self.protocol_var.get()
        if protocol == "TCP":
            threading.Thread(target=self.receive_file_tcp, args=(host, port)).start()
        elif protocol == "UDP":
            threading.Thread(target=self.receive_file_udp, args=(host, port)).start()

    def download_file(self):
        selected_file = self.listbox_received_files.get(tk.ACTIVE)
        if selected_file:
            save_path = filedialog.asksaveasfilename(initialfile=selected_file)
            if save_path:
                original_path = self.file_paths[selected_file]
                with open(original_path, 'rb') as src, open(save_path, 'wb') as dst:
                    dst.write(src.read())
                messagebox.showinfo("下载完成", f"文件 {selected_file} 下载完成")

    def show_files(self, file_list):
        self.listbox_file_display.delete(0, tk.END)
        for file in file_list:
            self.listbox_file_display.insert(tk.END, file)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileReceiver(root)
    root.mainloop()