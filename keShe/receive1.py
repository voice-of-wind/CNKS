import socket
import os
import tkinter as tk
from tkinter import messagebox, filedialog,ttk
import uuid
import hashlib
import time
import threading

# Todo
# 2.多线程TCP完成
# 4.按照要求进行绘图
# 5.修改进度百分比不准的问题
# 6.测试其他类型文件是否可以传输




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
    elif file_extension in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
        return 4
    elif file_extension in ['.zip', '.rar', '.7z']:
        return 5
    else:
        return -1

# endregion

# 接收文件的函数（TCP）
def receive_file_tcp(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("等待连接...")
        conn, addr = s.accept()
        print(f"连接来自: {addr}")
        save_paths = []
        file_names = []
        buffer_size = 1024 * 8
        vaildData = ""
        remainData = False
        with conn:
            while True:
                if not remainData:
                    data = conn.recv(buffer_size)
                    # data = data.decode('utf-8')
                    # 不要对数据进行utf-8解码，因为数据可能包含非utf-8字符 所以切割时 以及保存时 都不要解码
                    remainData = False
                    fileType = get_file_type(data)
                    print(f"当前文件类型: {fileType}")
                    # 如果接收到的数据为空，则退出循环
                    if not data:
                        break


                if fileType != -1:
                    # 这里的vaild都是字节流
                    vaildData = data.split(beginFs[fileType])[1]
                    print(data)
                    datas = vaildData.split(splitF,3)
                    file_name = datas[1].decode('utf-8')
                    print(f"当前接收文件: {file_name}")
                    unique_id = uuid.uuid4()
                    file_name = str(unique_id) + "-" + file_name
                    save_path = os.path.join(f"../receive/{fileTypes[fileType]}", file_name)
                    # 文件大小数据
                    file_size = int(datas[2].decode('utf-8'))
                    
                    fileData = datas[3]
                    dir_path = os.path.dirname(save_path)
                    if not os.path.exists(dir_path):
                        print("创建目录")
                        os.makedirs(dir_path)
                    # else:
                    fileType = -1
                    received_size = 0
                    start_time = time.time()
                    speed = 0
                    with open(save_path, 'wb') as f:
                        f.write(fileData)
                        received_size += len(fileData)
                        while True:
                            # 如果文件头后面跟的有数据
                            chunk = conn.recv(buffer_size)
                            if endF in chunk:
                                remains = chunk.split(endF)[0]
                                f.write(remains)
                                if len(chunk.split(endF)) > 1 and len(chunk.split(endF)[1]) > 10:
                                    remainData = True
                                    # data就是要么为空 要么 为是下一个文件的文件头
                                    data = chunk.split(endF)[1]
                                    print(f"最后一段数据: {chunk}")
                                    fileType = get_file_type(data)
                                    print(f"当前文件类型: {fileType}")
                                break
                            else:
                                f.write(chunk)
                                received_size += len(chunk)
                                progress = (received_size / file_size) * 100
                                progress_var.set(progress)
                                progress_label.config(text=f"{progress:.2f}%")
                                elapsed_time = time.time() - start_time
                                if elapsed_time>0:
                                    speed = received_size / elapsed_time / 1024  # KB/s
                                speed_label.config(text=f"接收速率: {speed:.2f} KB/s")
                                root.update_idletasks()
                    save_paths.append(save_path)
                    file_names.append(file_name)
                    print(f"{file_name} 文件接收完成")
                else:
                    break
    print("接收完成")
    return save_paths, file_names

# 接收文件的函数（UDP）
def receive_file_udp(host, port):
    udpRecSize = int(1024*8)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((host, port))
        print("等待连接...")
        save_paths = []
        file_names = []

        while True:
            data, addr = s.recvfrom(udpRecSize)
            received_size = 0
            start_time = time.time()

            # 数据的后32位是利用前面内容生成的MD5校验和
            if hashlib.md5(data[:-32]).hexdigest().encode('utf-8') == data[-32:]:
                s.sendto(b'ACK', addr)
            else:
                print("校验和错误，丢弃数据包")
                s.sendto(b'NACK', addr)

            if allEnd in data:
                break
            # 保证每次开头必须要能传输没问题
            print(data)
            fileType = get_file_type(data)
            print(f"当前文件类型: {fileType}")
            if fileType != -1:
                vaildData = data.split(beginFs[fileType])[1]
                datas = vaildData.split(splitF, 3)
                file_name = datas[1].decode('utf-8')
                print(f"当前接收文件: {file_name}")
                unique_id = uuid.uuid4()
                file_name = str(unique_id) + "-" + file_name
                save_path = os.path.join(f"../receive/{fileTypes[fileType]}", file_name)
                file_size = int(datas[2])
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

                    while True:
                        chunk, addr = s.recvfrom(udpRecSize)
                        data, checksum = chunk[:-32], chunk[-32:]
                        if hashlib.md5(data).hexdigest().encode('utf-8') == checksum:
                            s.sendto(b'ACK', addr)
                        else:
                            print("校验和错误，丢弃数据包NACK")
                            s.sendto(b'NACK', addr)

                        if endF in chunk:
                            print(f"最后一段数据: {chunk}")
                            break
                        else:
                            s.sendto(b'ACK', addr)
                            received_size += len(filedata)
                            progress = (received_size / file_size) * 100
                            progress_var.set(progress)
                            progress_label.config(text=f"{progress:.2f}%")
                            elapsed_time = time.time() - start_time

                            if elapsed_time>0:
                                speed = received_size / elapsed_time / 1024  # KB/s
                            speed_label.config(text=f"接收速率: {speed:.2f} KB/s")
                            root.update_idletasks()
                            f.write(data)

                save_paths.append(save_path)
                file_names.append(file_name)
                print(f"{file_name} 文件接收完成")
            else:
                print("未识别的文件类型")
                break
    print("接收完成")
    return save_paths, file_names

# 有进程 如果数据为空 是不是就能说明所有文件都接收完毕了？
# 发送端发送一个单文件结束符 
# 当接收端的有一个子进程接收到这个符号时 就说明这个文件接收完毕 该子进程即可发送ACK给发送端 
# 如果发送端收到ACK则发送下一个文件的头部信息
# 如果接收端收到的是allEnd 则说明所有文件接收完毕
# 对应子进程在其他子进程接收完毕后阻塞所有进程


# 如果数据里有结束标识符 则告诉发送方可以发送下一个文件

# 如果数据里有全部文件发送完成的标识符 
def receive_file_tcp_multithread(host, port, num_threads=1):
    buffer_size = 1024 * 4
    
    def receive_chunk(conn, lock):
        start = 0
        while True:
            # 每次接收一个数据块，大小为缓冲区大小
            header = conn.recv(buffer_size)
            # if not header:
            #     print("接收数据为空")
            #     break
            # 如果接收到的数据为空，则退出循环


            # 判断是否是分割符（splitF），如果是，解析文件信息
            if splitF in header:
                header, chunk = header.split(splitF, 1)
                file_id, thread_id, chunk_start = header.decode('utf-8').split(':')
                chunk_start = int(chunk_start)
                
                # 解析文件类型并确定保存路径
                fileType = get_file_type_str(file_id)
                # uuid1 = str(uuid.uuid1())
                save_path = f"../receive/{fileTypes[fileType]}/{file_id}"
                # 不存在则创建目录
                dir_path = os.path.dirname(save_path)
                if not os.path.exists(dir_path):
                    print("创建目录")
                    os.makedirs(dir_path)

                # 使用锁确保文件写入是互斥的
                with lock:
                    # 如果文件不存在，则创建文件
                    if not os.path.exists(save_path):
                        with open(save_path, 'wb') as f:
                            pass
                    with open(save_path, 'r+b') as f:
                        f.seek(chunk_start)  # 移动到指定位置写入
                        f.write(chunk)  # 写入文件块
                        start += len(chunk)



            # 判断是否接收到文件结束标识符
            if b'###END###' in header:
                print(f"接收到文件结束符")
                conn.send(b'ACK')  # 发送ACK给发送端确认文件接收完毕

            # 判断是否接收到所有文件结束标识符
            if b'AllEnd' in header:
                print("接收到所有文件结束符")
                conn.send(b'ACK')  # 发送ACK给发送端确认所有文件接收完毕
                break  # 退出循环，所有文件传输完毕

    # 创建并绑定服务器套接字
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("等待连接...")

        lock = threading.Lock()  # 创建锁，确保文件写入是互斥的
        threads = []

        # 接收每个线程的连接并启动接收线程
        for i in range(num_threads):
            conn, addr = s.accept()
            print(f"线程 {i} 连接来自: {addr}")
            # 每个连接启动一个新的线程来处理文件接收
            thread = threading.Thread(target=receive_chunk, args=(conn, lock))
            threads.append(thread)
            thread.start()

        # 等待所有线程执行完成
        for thread in threads:
            thread.join()

        print("接收完成")


def start_receiving():
    host = entry_host_receive.get()
    port = int(entry_port_receive.get())
    protocol = protocol_var.get()
    print(protocol)
    save_paths = []
    if protocol == "TCP":
        save_paths, file_names = receive_file_tcp(host, port)
    elif protocol == "UDP":
        save_paths, file_names = receive_file_udp(host, port)
    elif protocol == "TCP_multiThread":
        num_threads = int(entry_threads.get())
        threading.Thread(target=receive_file_tcp_multithread, args=(host, port, num_threads)).start()

    if save_paths:
        for i in range(len(save_paths)):
            listbox_received_files.insert(tk.END, file_names[i])
            file_paths[file_names[i]] = save_paths[i]
            # 按文件类型分类显示
            file_type = get_file_type_str(file_names[i])
            if file_type == 0:
                img_files.append(file_names[i])
            elif file_type == 1:
                audio_files.append(file_names[i])
            elif file_type == 2:
                video_files.append(file_names[i])
            elif file_type == 3:
                text_files.append(file_names[i])
            elif file_type == 4:
                office_files.append(file_names[i])
            elif file_type == 5:
                zip_files.append(file_names[i])
        messagebox.showinfo("接收完成", f"文件接收完成")


def download_file():
    selected_file = listbox_received_files.get(tk.ACTIVE)
    if selected_file:
        save_path = filedialog.asksaveasfilename(initialfile=selected_file)
        if save_path:
            original_path = file_paths[selected_file]
            with open(original_path, 'rb') as src, open(save_path, 'wb') as dst:
                dst.write(src.read())
            messagebox.showinfo("下载完成", f"文件 {selected_file} 下载完成")


# 切换显示文件类型的函数
def show_files(file_list):
    listbox_file_display.delete(0, tk.END)
    for file in file_list:
        listbox_file_display.insert(tk.END, file)



#region 下面是GUI部分
# region全局变量
file_paths = {}
img_files = []
audio_files = []
video_files = []
office_files = []
text_files = []
zip_files = []
#endregion

# region创建主窗口
root = tk.Tk()
root.title("文件接收器")
# endregion

# 第一行：主机地址、端口号
frame_host_port = tk.Frame(root)
frame_host_port.pack(pady=10)

label_host_receive = tk.Label(frame_host_port, text="主机地址:")
label_host_receive.pack(side=tk.LEFT)
entry_host_receive = tk.Entry(frame_host_port, width=20)
entry_host_receive.pack(side=tk.LEFT, padx=5)
entry_host_receive.insert(0, "127.0.0.1")

label_port_receive = tk.Label(frame_host_port, text="端口号:")
label_port_receive.pack(side=tk.LEFT)
entry_port_receive = tk.Entry(frame_host_port, width=10)
entry_port_receive.pack(side=tk.LEFT, padx=5)
entry_port_receive.insert(0, "12000")

# 第二行：选择协议、线程数量、发送按钮
frame_protocol_threads = tk.Frame(root)
frame_protocol_threads.pack(pady=10)

label_protocol = tk.Label(frame_protocol_threads, text="选择协议:")
label_protocol.pack(side=tk.LEFT)
protocol_var = tk.StringVar(value="TCP_multiThread")
protocol_menu = ttk.Combobox(frame_protocol_threads, textvariable=protocol_var, values=["TCP", "UDP", "TCP_multiThread"], state="readonly")
protocol_menu.pack(side=tk.LEFT, padx=5)

label_threads = tk.Label(frame_protocol_threads, text="线程数量:")
label_threads.pack(side=tk.LEFT)
entry_threads = tk.Entry(frame_protocol_threads, width=10)
entry_threads.pack(side=tk.LEFT, padx=5)
entry_threads.insert(0, "1")  # 设置默认值

button_receive = tk.Button(frame_protocol_threads, text="开始接收", command=start_receiving)
button_receive.pack(side=tk.LEFT, padx=5)

# region接收到的文件显示区域
frame_received_files = tk.Frame(root)
frame_received_files.pack(pady=10)
label_received_files = tk.Label(frame_received_files, text="接收到的文件:")
label_received_files.pack()
listbox_received_files = tk.Listbox(frame_received_files, width=50, height=10)
listbox_received_files.pack()
# endregion

# region公共文件显示区域
frame_file_display = tk.Frame(root)
frame_file_display.pack(pady=10)
label_file_display = tk.Label(frame_file_display, text="文件显示:")
label_file_display.pack()
listbox_file_display = tk.Listbox(frame_file_display, width=50, height=10)
listbox_file_display.pack()
# endregion

# region切换显示文件类型的按钮
frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)
button_show_all = tk.Button(frame_buttons, text="所有文件", command=lambda: show_files(listbox_received_files.get(0, tk.END)))
button_show_all.pack(side=tk.LEFT, padx=5)
button_show_img = tk.Button(frame_buttons, text="图片文件", command=lambda: show_files(img_files))
button_show_img.pack(side=tk.LEFT, padx=5)
button_show_audio = tk.Button(frame_buttons, text="音频文件", command=lambda: show_files(audio_files))
button_show_audio.pack(side=tk.LEFT, padx=5)
button_show_video = tk.Button(frame_buttons, text="视频文件", command=lambda: show_files(video_files))
button_show_video.pack(side=tk.LEFT, padx=5)
button_show_office = tk.Button(frame_buttons, text="办公文件", command=lambda: show_files(office_files))
button_show_office.pack(side=tk.LEFT, padx=5)
button_show_text = tk.Button(frame_buttons, text="文本文件", command=lambda: show_files(text_files))
button_show_text.pack(side=tk.LEFT, padx=5)
button_show_zip = tk.Button(frame_buttons, text="压缩文件", command=lambda: show_files(zip_files))
button_show_zip.pack(side=tk.LEFT, padx=5)
# endregion

# region下载文件按钮
button_download = tk.Button(root, text="下载选中文件", command=download_file)
button_download.pack(pady=20)
# endregion

# 进度条、进度百分比标签和接收速率标签放在一行
frame_progress = tk.Frame(root)
frame_progress.pack(pady=10)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame_progress, variable=progress_var, maximum=100)
progress_bar.pack(side=tk.LEFT, padx=5)

progress_label = tk.Label(frame_progress, text="0%")
progress_label.pack(side=tk.LEFT, padx=5)

speed_label = tk.Label(frame_progress, text="接收速率: 0 KB/s")
speed_label.pack(side=tk.LEFT, padx=5)


# 运行主循环
root.mainloop()
# endregion