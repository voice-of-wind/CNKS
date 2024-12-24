import socket
import os
import tkinter as tk
from tkinter import messagebox, filedialog,ttk
import uuid
import hashlib
import time
import threading
import queue
from concurrent.futures import ThreadPoolExecutor  # 导入ThreadPoolExecutor

# Todo
# 小bug使用tcp协议 小文件传输放在中间导致下一个文件接收不到
# 修改udp部分
# 1.改成线程启动函数 改成以类的形式 合并成一个文件收发器 提供文件校验功能
# 4.按照要求进行绘图
# 5.修改进度udp 和 tcp 单线程百分比不准的问题
# 6.测试其他类型文件是否可以传输

THREADS = 3


# region规定一个标识符用来区分发送文件的开头
beginImgF = b"#####*****img#####*****"
beginAudioF = b"#####*****audio#####*****"
beginVideoF = b"#####*****video#####*****"
beginF = b"#####*****file#####*****"
beginOfficeF = b"#####*****office#####*****"
beginZipF = b"#####*****zip#####*****"

splitF = b"#####-----#####"
endF = b"#####*****end_of_file*****#####"
allEnd = b"#####*****all_end*****#####"
fileTypes = ["img", "audio", "video", "file", "office", "zip"]
beginFs = [beginImgF, beginAudioF, beginVideoF, beginF, beginOfficeF, beginZipF]

BUFFER_SIZE = 4 * 1024  # 设置缓冲区大小为4KB
LOCK = threading.Lock()  # 全局线程锁

res_file_names = []
res_save_paths = []

#endregion


# region获取文件类型 第一个是根据文件开始符获取文件类型编号 第二个是根据文件后缀名获取文件类型编号0:img 1:audio 2:video 3:file 4:office 5:zip

def get_file_type(data):

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

def get_file_type_str(file_path):
    file_name, file_extension = os.path.splitext(file_path)
    if file_extension in ['.png', '.jpg', '.jpeg', '.gif']:
        return 0
    elif file_extension in ['.mp3', '.wav', '.flac']:
        return 1
    elif file_extension in ['.mp4', '.avi', '.mov']:
        return 2
    elif file_extension in ['.txt']:
        return 3
    elif file_extension in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx' ,'.pdf']:
        return 4
    elif file_extension in ['.zip', '.rar', '.7z']:
        return 5
    else:
        return -1

# endregion

class FileReceiver:
    def __init__(self):
        self.THREADS = 6
        self.BUFFER_SIZE = 4 * 1024
        self.LOCK = threading.Lock()
        self.res_file_names = []
        self.res_save_paths = []
        self.endflag = 0
        self.flag_lock = threading.Lock()
        self.received_size = 0
        self.start_time1 = 0
        self.file_size1 = 0

        self.finish_event = threading.Event()

        # 用来计算文件的传输速度
        self.cal_file_size = 0
        self.file_start_time = 0
        self.file_end_time = 0

        # 记录多个文件的大小
        self.file_sizes = []

    def set_endflag(self, value):
        with self.flag_lock:
            self.endflag = value

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
        elif file_extension in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx','.pdf']:
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
            buffer_size = 1024 * 8 * 2
            vaildData = ""
            remainData = False

            self.file_start_time = time.time()
            with conn:
                while True:
                    if not remainData:
                        data = conn.recv(buffer_size)
                        remainData = False
                        fileType = self.get_file_type(data)
                        print(f"当前文件类型: {fileType}")
                        if not data:
                            break

                    if fileType != -1:
                        received_size = 0
                        start_time = time.time()
                        vaildData = data.split(beginFs[fileType])[1]
                        print(data)
                        datas = vaildData.split(splitF, 3)
                        file_name = datas[1].decode('utf-8')
                        print(f"当前接收文件: {file_name}")
                        unique_id = uuid.uuid4()

                        file_name = str(unique_id) + "-" + file_name
                        save_path = os.path.join(f"../receive/{fileTypes[fileType]}", file_name)

                        if file_name not in self.res_file_names:
                            self.res_file_names.append(file_name)
                        if save_path not in self.res_save_paths:
                            self.res_save_paths.append(save_path)

                        file_size = int(datas[2].decode('utf-8'))

                        self.file_sizes.append(file_size)

                        fileData = datas[3]
                        dir_path = os.path.dirname(save_path)
                        if not os.path.exists(dir_path):
                            print("创建目录")
                            os.makedirs(dir_path)
                        fileType = -1

                        speed = 0
                        with open(save_path, 'wb') as f:
                            f.write(fileData)
                            received_size += len(fileData)
                            while True:
                                chunk = conn.recv(buffer_size)
                                if endF in chunk:
                                    remains = chunk.split(endF)[0]

                                    received_size += len(remains)
                                    progress = (received_size / file_size) * 100
                                    self.ui.progress_var.set(progress)
                                    self.ui.progress_label.config(text=f"{progress:.2f}%")
                                    elapsed_time = time.time() - start_time
                                    if elapsed_time > 0:
                                        speed = received_size / elapsed_time / 1024  # KB/s
                                    self.ui.speed_label.config(text=f"接收速率: {speed:.2f} KB/s")
                                    root.update_idletasks()

                                    f.write(remains)

                                    if len(chunk.split(endF)) > 1 and len(chunk.split(endF)[1]) > 10:
                                        remainData = True
                                        data = chunk.split(endF)[1]
                                        print(f"最后一段数据: {chunk}")
                                        fileType = self.get_file_type(data)
                                        print(f"当前文件类型: {fileType}")
                                    break
                                else:
                                    f.write(chunk)
                                    received_size += len(chunk)
                                    progress = (received_size / file_size) * 100
                                    self.ui.progress_var.set(progress)
                                    self.ui.progress_label.config(text=f"{progress:.2f}%")
                                    elapsed_time = time.time() - start_time
                                    if elapsed_time > 0:
                                        speed = received_size / elapsed_time / 1024  # KB/s
                                    self.ui.speed_label.config(text=f"接收速率: {speed:.2f} KB/s")
                                    root.update_idletasks()
                        print(f"{file_name} 文件接收完成")
                        self.ui.progress_var.set(100)
                        self.ui.progress_label.config(text="100%")
                        root.update_idletasks()
                    else:
                        break
        self.finish_event.set()
        print("接收完成")

    def receive_file_udp(self, host, port):
        udpRecSize = int(1024 * 4 * 8)
        # udpRecSize = int(1000)
        si = 0
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((host, port))
            print("等待连接...")
            while True:
                data, addr = s.recvfrom(udpRecSize)

                if si == 0:
                    self.file_start_time = time.time()
                    si += 1

                received_size = 0
                
                start_time = time.time()

                nowIndex = 0
                if hashlib.md5(data[:-32] + str(nowIndex).encode('utf-8')).hexdigest().encode('utf-8') == data[-32:]:
                    s.sendto(b'ACK', addr)
                    nowIndex += 1
                else:
                    print(f"校验和错误，丢弃数据包 当前块数{nowIndex}")
                    s.sendto(b'NACK', addr)

                if allEnd in data:
                    print("allEnd in data")
                    break
                print(data)
                fileType = self.get_file_type(data)
                print(f"当前文件类型: {fileType}")
                if fileType != -1:
                    vaildData = data.split(beginFs[fileType])[1]
                    datas = vaildData.split(splitF, 3)
                    file_name = datas[1].decode('utf-8')
                    print(f"当前接收文件: {file_name}")
                    unique_id = uuid.uuid4()
                    file_name = str(unique_id) + "-" + file_name
                    save_path = os.path.join(f"../receive/{fileTypes[fileType]}", file_name)
                    if file_name not in self.res_file_names:
                        self.res_file_names.append(file_name)
                    if save_path not in self.res_save_paths:
                        self.res_save_paths.append(save_path)
                    file_size = int(datas[2])
                    self.file_sizes.append(file_size)

                    fileData = datas[3]
                    dir_path = os.path.dirname(save_path)
                    if not os.path.exists(dir_path):
                        print("创建目录")
                        os.makedirs(dir_path)
                    fileType = -1
                    speed = 0
                    with open(save_path, 'wb') as f:
                        filedata, checksum = fileData[:-32], fileData[-32:]
                        f.write(filedata)
                        received_size += len(filedata)
                        while True:
                            while True:
                                chunk, addr = s.recvfrom(udpRecSize)
                                data, checksum = chunk[:-32], chunk[-32:]
                                if hashlib.md5(data + str(nowIndex).encode('utf-8')).hexdigest().encode('utf-8') == checksum:
                                    s.sendto(b'ACK', addr)
                                    nowIndex += 1
                                    break
                                else:
                                    print(f"校验和错误，丢弃数据包NACK 当前块数{nowIndex}")
                                    s.sendto(b'NACK', addr)

                            if endF in chunk:
                                print(f"最后一段数据: {chunk}")
                                break
                            else:
                                received_size += len(data)
                                progress = (received_size / file_size) * 100
                                self.ui.progress_var.set(progress)
                                self.ui.progress_label.config(text=f"{progress:.2f}%")
                                elapsed_time = time.time() - start_time

                                if elapsed_time > 0:
                                    speed = received_size / elapsed_time / 1024  # KB/s
                                self.ui.speed_label.config(text=f"接收速率: {speed:.2f} KB/s")
                                root.update_idletasks()
                                f.write(data)

                    print(f"{file_name} 文件接收完成")
                    self.ui.progress_var.set(100)
                    self.ui.progress_label.config(text="100%")
                    root.update_idletasks()
                else:
                    print("未识别的文件类型")
                    break
        self.finish_event.set()
        print("接收完成")

    def receive_chunk(self, conn, lock, prefix):
        buffer_size = 1024 * 4 * 8
        remote_port = conn.getpeername()[1]
        while True:
            header = conn.recv(buffer_size)
            if header == b'':
                break
            if b'AllEnd' in header:
                self.set_endflag(-1)
                break
            if b"::" in header:
                header, chunk = header.split(b"::", 1)
                try:
                    file_id, end, chunk_start, file_size = header.decode('utf-8').split(':')
                except:
                    print("解码错误")
                    print(header)

                self.file_size1 = int(file_size)

                if self.file_size1 not in self.file_sizes:
                    self.file_sizes.append(self.file_size1)
                
                end = int(end)
                chunk_start = int(chunk_start)
                fileType = self.get_file_type_str(file_id)
                save_path = f"../receive/{fileTypes[fileType]}/{prefix}-{file_id}"

                if f"{fileTypes[fileType]}/{prefix}-{file_id}" not in self.res_file_names:
                    self.res_file_names.append(f"{fileTypes[fileType]}/{prefix}-{file_id}")

                dir_path = os.path.dirname(save_path)
                write_size = len(chunk)
                with lock:
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path)
                    if not os.path.exists(save_path):
                        with open(save_path, 'wb') as f:
                            pass
                    with open(save_path, 'r+b') as f:
                        f.seek(chunk_start)
                        f.write(chunk)

                self.received_size += write_size
                progress = (self.received_size / self.file_size1) * 100
                self.ui.progress_var.set(progress)
                elapsed_time = time.time() - self.start_time1
                if elapsed_time > 0:
                    speed = self.received_size / elapsed_time / 1024
                self.ui.speed_label.config(text=f"接收速率: {speed:.2f} KB/s")
                self.ui.progress_label.config(text=f"{progress:.2f}%")
                root.update_idletasks()

                if chunk_start + write_size == end:
                    conn.send(b'ACK')
                    print(f"发送ACK到端口{remote_port}")
                    self.ui.progress_var.set(100)
                    self.ui.progress_label.config(text="100%")
                    root.update_idletasks()
                    break

    def receive_file_tcp_multithread(self, host, port, num_threads=THREADS):
        lock = threading.Lock()
        threads = []
        si = 0
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                s.listen()
                print("等待连接...")
                prifix = str(uuid.uuid4())
                conns = []

                for i in range(num_threads):
                    conn, addr = s.accept()
                    conns.append(conn)

                if si == 0:
                    self.file_start_time = time.time()
                    print("文件开始接收时间:", self.file_start_time)
                    si += 1

                self.start_time1 = time.time()
                for i in range(num_threads):
                    conn = conns[i]
                    thread = threading.Thread(target=self.receive_chunk, args=(conn, lock, prifix))
                    threads.append(thread)
                    thread.start()

                for thread in threads:
                    print(f"启动线程 {i}")
                    thread.join()

                threads.clear()
                conns.clear()
                self.received_size = 0
                self.start_time1 = 0
                print("完成一个文件接收")

                if self.endflag == -1:
                    print("所有文件接收完成")
                    self.set_endflag(0)
                    self.finish_event.set()
                    return

    def wait_for_completion(self):
            # 等待子线程完成
            self.finish_event.wait()
            # 计算本次文件传输速度
            self.file_end_time = time.time()
            print("文件结束接收时间:", self.file_end_time)
            # 计算文件传输速度
            elapsed_time = self.file_end_time - self.file_start_time
            if elapsed_time > 0:
                for i in range(len(self.file_sizes)):
                    self.cal_file_size += self.file_sizes[i]
                print("本次传输文件大小:", self.cal_file_size)
                speed = self.cal_file_size / elapsed_time / 1024
            
            # 将速度和线程数以一定格式追加写到文件中
            with open("speed.txt", 'a') as f:
                f.write(f"{speed:.2f} KB/s, {self.THREADS} threads\n")
            
            # 计算完后清空相关数据项
            self.cal_file_size = 0
            self.file_start_time = 0
            self.file_end_time = 0
            self.file_sizes.clear()


            # 子线程完成后执行的代码
            if self.res_file_names:
                for i in range(len(self.res_file_names)):
                    self.ui.listbox_received_files.insert(tk.END, self.res_file_names[i])
                    self.ui.file_paths[self.res_file_names[i]] = self.res_file_names[i]
                    file_type = self.get_file_type_str(self.res_file_names[i])
                    if file_type == 0:
                        self.ui.img_files.append(self.res_file_names[i])
                    elif file_type == 1:
                        self.ui.audio_files.append(self.res_file_names[i])
                    elif file_type == 2:
                        self.ui.video_files.append(self.res_file_names[i])
                    elif file_type == 3:
                        self.ui.text_files.append(self.res_file_names[i])
                    elif file_type == 4:
                        self.ui.office_files.append(self.res_file_names[i])
                    elif file_type == 5:
                        self.ui.zip_files.append(self.res_file_names[i])
                messagebox.showinfo("接收完成", f"文件接收完成")

    def start_receiving(self):
        host = self.ui.entry_host_receive.get()
        port_text = self.ui.entry_port_receive.get()
        if not host or not port_text:
            messagebox.showerror("错误", "请检查主机地址和端口号！")
            return
        port = int(port_text)
        protocol = self.ui.protocol_var.get()

        if protocol == "TCP":
            receive_thread = threading.Thread(target=self.receive_file_tcp, args=(host, port))
        elif protocol == "UDP":
            receive_thread = threading.Thread(target=self.receive_file_udp, args=(host, port))
        elif protocol == "TCP_multiThread":
            num_threads = int(self.ui.entry_threads.get())
            self.THREADS = num_threads
            print(f"线程数{self.THREADS}")
            receive_thread = threading.Thread(target=self.receive_file_tcp_multithread, args=(host, port, num_threads))
        receive_thread.start()
        threading.Thread(target=self.wait_for_completion).start()
        # receive_thread.join()  # 等待子线程完成




    def download_file(self):
        selected_file = self.ui.listbox_received_files.get(tk.ACTIVE)
        if selected_file:
            save_path = filedialog.asksaveasfilename(initialfile=selected_file)
            if save_path:
                original_path = self.ui.file_paths[selected_file]
                with open(original_path, 'rb') as src, open(save_path, 'wb') as dst:
                    dst.write(src.read())
                messagebox.showinfo("下载完成", f"文件 {selected_file} 下载完成")

    def show_files(self, file_list):
        self.ui.listbox_file_display.delete(0, tk.END)
        for file in file_list:
            self.ui.listbox_file_display.insert(tk.END, file)

    def clear_files(self, fileRec):
        self.res_file_names = []
        self.res_save_paths = []

        fileRec.img_files = []
        fileRec.audio_files = []
        fileRec.video_files = []
        fileRec.office_files = []
        fileRec.text_files = []
        fileRec.zip_files = []

        self.ui.listbox_file_display.delete(0, tk.END)
        self.ui.listbox_received_files.delete(0, tk.END)
        messagebox.showinfo("清空完成", f"文件列表清空完成")

class FileReceiverUI:
    def __init__(self, root, file_receiver):
        self.file_receiver = file_receiver
        self.file_receiver.ui = self

        self.file_paths = {}
        self.img_files = []
        self.audio_files = []
        self.video_files = []
        self.office_files = []
        self.text_files = []
        self.zip_files = []

        root.title("文件接收器")

        frame_host_port = tk.Frame(root)
        frame_host_port.pack(pady=10)

        label_host_receive = tk.Label(frame_host_port, text="主机地址:")
        label_host_receive.pack(side=tk.LEFT)
        self.entry_host_receive = tk.Entry(frame_host_port, width=20)
        self.entry_host_receive.pack(side=tk.LEFT, padx=5)
        self.entry_host_receive.insert(0, "127.0.0.1")

        label_port_receive = tk.Label(frame_host_port, text="端口号:")
        label_port_receive.pack(side=tk.LEFT)
        self.entry_port_receive = tk.Entry(frame_host_port, width=10)
        self.entry_port_receive.pack(side=tk.LEFT, padx=5)
        self.entry_port_receive.insert(0, "12345")

        frame_protocol_threads = tk.Frame(root)
        frame_protocol_threads.pack(pady=10)

        label_protocol = tk.Label(frame_protocol_threads, text="选择协议:")
        label_protocol.pack(side=tk.LEFT)
        self.protocol_var = tk.StringVar(value="TCP_multiThread")
        protocol_menu = ttk.Combobox(frame_protocol_threads, textvariable=self.protocol_var, values=["TCP", "UDP", "TCP_multiThread"], state="readonly")
        protocol_menu.pack(side=tk.LEFT, padx=5)

        label_threads = tk.Label(frame_protocol_threads, text="线程数量:")
        label_threads.pack(side=tk.LEFT)
        self.entry_threads = tk.Entry(frame_protocol_threads, width=10)
        self.entry_threads.pack(side=tk.LEFT, padx=5)
        self.entry_threads.insert(0, str(THREADS))

        button_receive = tk.Button(frame_protocol_threads, text="开始接收", command=self.file_receiver.start_receiving)
        button_receive.pack(side=tk.LEFT, padx=5)

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
        button_show_all = tk.Button(frame_buttons, text="所有文件", command=lambda: self.file_receiver.show_files(self.listbox_received_files.get(0, tk.END)))
        button_show_all.pack(side=tk.LEFT, padx=5)
        button_show_img = tk.Button(frame_buttons, text="图片文件", command=lambda: self.file_receiver.show_files(self.img_files))
        button_show_img.pack(side=tk.LEFT, padx=5)
        button_show_audio = tk.Button(frame_buttons, text="音频文件", command=lambda: self.file_receiver.show_files(self.audio_files))
        button_show_audio.pack(side=tk.LEFT, padx=5)
        button_show_video = tk.Button(frame_buttons, text="视频文件", command=lambda: self.file_receiver.show_files(self.video_files))
        button_show_video.pack(side=tk.LEFT, padx=5)
        button_show_office = tk.Button(frame_buttons, text="办公文件", command=lambda: self.file_receiver.show_files(self.office_files))
        button_show_office.pack(side=tk.LEFT, padx=5)
        button_show_text = tk.Button(frame_buttons, text="文本文件", command=lambda: self.file_receiver.show_files(self.text_files))
        button_show_text.pack(side=tk.LEFT, padx=5)
        button_show_zip = tk.Button(frame_buttons, text="压缩文件", command=lambda: self.file_receiver.show_files(self.zip_files))
        button_show_zip.pack(side=tk.LEFT, padx=5)

        # 创建一个框架来容纳按钮
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)

        # 下载选中文件按钮
        button_download = tk.Button(button_frame, text="下载选中文件", command=self.file_receiver.download_file)
        button_download.pack(side=tk.LEFT, padx=10)

        # 清空文件列表按钮
        button_clear = tk.Button(button_frame, text="清空文件列表", command=lambda: self.file_receiver.clear_files(self))
        button_clear.pack(side=tk.LEFT, padx=10)


        frame_progress = tk.Frame(root)
        frame_progress.pack(pady=10)

        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(frame_progress, variable=self.progress_var, maximum=100)
        progress_bar.pack(side=tk.LEFT, padx=5)

        self.progress_label = tk.Label(frame_progress, text="0%")
        self.progress_label.pack(side=tk.LEFT, padx=5)

        self.speed_label = tk.Label(frame_progress, text="接收速率: 0 KB/s")
        self.speed_label.pack(side=tk.LEFT, padx=5)

if __name__ == "__main__":
    root = tk.Tk()
    file_receiver = FileReceiver()
    ui = FileReceiverUI(root, file_receiver)
    root.mainloop()
