import socket
import os
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import uuid
import threading

# 规定一个标识符用来区分发送文件的开头
beginImgF = b"#####*****img#####*****"
beginAudioF = b"#####*****audio#####*****"
beginVideoF = b"#####*****video#####*****"
beginOfficeF = b"#####*****office#####*****"
beginZipF = b"#####*****zip#####*****"
beginF = b"#####*****file#####*****"
splitF = b"#####-----#####"
endF = b"#####*****end_of_file*****#####"
fileTypes = ["img", "audio", "video", "file", "office", "zip"]
beginFs = [beginImgF, beginAudioF, beginVideoF, beginF, beginOfficeF, beginZipF]

# 根据文件后缀确定文件类型从而发送对应标识符
def get_file_type(file_path):
    file_name, file_extension = os.path.splitext(file_path)
    if file_extension in ['.png', '.jpg', '.jpeg', '.gif']:
        return beginImgF
    elif file_extension in ['.mp3', '.wav', '.flac']:
        return beginAudioF
    elif file_extension in ['.mp4', '.avi', '.mov']:
        return beginVideoF
    elif file_extension in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
        return beginOfficeF
    elif file_extension in ['.txt']:
        return beginF
    elif file_extension in ['.zip', '.rar', '.7z']:
        return beginZipF
    else:
        return -1

# 发送文件的函数
def send_file_tcp(file_paths, host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            typeF = get_file_type(file_path)
            s.sendall(typeF + splitF + file_name.encode('utf-8') + splitF)
            with open(file_path, 'rb') as f:
                while (chunk := f.read(1024)):
                    s.sendall(chunk)
            s.sendall(endF)
            print(f"{file_name} 文件发送完成")

# 选择文件的函数
def select_files():
    file_paths = filedialog.askopenfilenames()
    if file_paths:
        for file_path in file_paths:
            listbox_files.insert(tk.END, file_path)

# 发送文件的函数
def send_files():
    file_paths = listbox_files.get(0, tk.END)
    host = entry_host_send.get()
    port = int(entry_port_send.get())
    threading.Thread(target=send_file_tcp, args=(file_paths, host, port)).start()
    listbox_files.delete(0, tk.END)

# 接收文件的函数
def receive_file_tcp(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("等待连接...")
        conn, addr = s.accept()
        print(f"连接来自: {addr}")
        save_paths = []
        file_names = []
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                try:
                    data = data.decode('utf-8')
                    fileType = get_file_type(data)
                    if fileType != -1:
                        vaildData = data.split(beginF)[0]
                        file_name = vaildData.split(splitF)[1]
                        unique_id = uuid.uuid4()
                        file_name = str(unique_id) + "-" + file_name
                        save_path = os.path.join(f"../receive/{fileTypes[fileType]}", file_name)

                        dir_path = os.path.dirname(save_path)
                        if not os.path.exists(dir_path):
                            print("创建目录")
                            os.makedirs(dir_path)

                        with open(save_path, 'wb') as f:
                            while True:
                                chunk = conn.recv(1024)
                                if endF in chunk:
                                    chunk = chunk.split(endF)[0]
                                    f.write(chunk)
                                    break
                                f.write(chunk)

                        save_paths.append(save_path)
                        file_names.append(file_name)
                        print(f"{file_name} 文件接收完成")
                    else:
                        print("未识别的文件类型")
                except UnicodeDecodeError:
                    print("接收到的数据无法解码，可能是文件传输过程中出现问题")
                    continue
    return save_paths, file_names

# 开始接收文件的函数
def start_receiving():
    host = entry_host_receive.get()
    port = int(entry_port_receive.get())
    threading.Thread(target=receive_files_thread, args=(host, port)).start()

def receive_files_thread(host, port):
    save_paths, file_names = receive_file_tcp(host, port)
    if save_paths:
        for i in range(len(save_paths)):
            listbox_received_files.insert(tk.END, file_names[i])
            file_paths[file_names[i]] = save_paths[i]
            # 按文件类型分类显示
            file_type = get_file_type(file_names[i])
            if file_type == beginImgF:
                img_files.append(file_names[i])
            elif file_type == beginAudioF:
                audio_files.append(file_names[i])
            elif file_type == beginVideoF:
                video_files.append(file_names[i])
            elif file_type == beginOfficeF:
                office_files.append(file_names[i])
            elif file_type == beginF:
                text_files.append(file_names[i])
            elif file_type == beginZipF:
                zip_files.append(file_names[i])
        messagebox.showinfo("接收完成", f"文件接收完成")

# 下载文件的函数
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

file_paths = {}
img_files = []
audio_files = []
video_files = []
office_files = []
text_files = []
zip_files = []

# 创建主窗口
root = tk.Tk()
root.title("文件传输器")

# 创建选项卡
tab_control = ttk.Notebook(root)
tab_send = ttk.Frame(tab_control)
tab_receive = ttk.Frame(tab_control)
tab_control.add(tab_send, text="发送文件")
tab_control.add(tab_receive, text="接收文件")
tab_control.pack(expand=1, fill="both")

# 发送文件选项卡
frame_file = tk.Frame(tab_send)
frame_file.pack(pady=10)
label_file_path = tk.Label(frame_file, text="文件路径:")
label_file_path.pack(side=tk.LEFT)
button_browse = tk.Button(frame_file, text="浏览", command=select_files)
button_browse.pack(side=tk.LEFT)

frame_files = tk.Frame(tab_send)
frame_files.pack(pady=10)
label_files = tk.Label(frame_files, text="选中的文件:")
label_files.pack()
listbox_files = tk.Listbox(frame_files, width=50, height=10)
listbox_files.pack()

frame_host_send = tk.Frame(tab_send)
frame_host_send.pack(pady=10)
label_host_send = tk.Label(frame_host_send, text="主机地址:")
label_host_send.pack(side=tk.LEFT)
entry_host_send = tk.Entry(frame_host_send, width=20)
entry_host_send.pack(side=tk.LEFT, padx=5)
entry_host_send.insert(0, "127.0.0.1")

frame_port_send = tk.Frame(tab_send)
frame_port_send.pack(pady=10)
label_port_send = tk.Label(frame_port_send, text="端口号:")
label_port_send.pack(side=tk.LEFT)
entry_port_send = tk.Entry(frame_port_send, width=10)
entry_port_send.pack(side=tk.LEFT, padx=5)
entry_port_send.insert(0, "12000")

button_send = tk.Button(tab_send, text="发送", command=send_files)
button_send.pack(pady=20)

# 接收文件选项卡
frame_host_receive = tk.Frame(tab_receive)
frame_host_receive.pack(pady=10)
label_host_receive = tk.Label(frame_host_receive, text="主机地址:")
label_host_receive.pack(side=tk.LEFT)
entry_host_receive = tk.Entry(frame_host_receive, width=20)
entry_host_receive.pack(side=tk.LEFT, padx=5)
entry_host_receive.insert(0, "127.0.0.1")

frame_port_receive = tk.Frame(tab_receive)
frame_port_receive.pack(pady=10)
label_port_receive = tk.Label(frame_port_receive, text="端口号:")
label_port_receive.pack(side=tk.LEFT)
entry_port_receive = tk.Entry(frame_port_receive, width=10)
entry_port_receive.pack(side=tk.LEFT, padx=5)
entry_port_receive.insert(0, "12000")

button_receive = tk.Button(tab_receive, text="开始接收", command=start_receiving)
button_receive.pack(pady=20)

frame_received_files = tk.Frame(tab_receive)
frame_received_files.pack(pady=10)
label_received_files = tk.Label(frame_received_files, text="接收到的文件:")
label_received_files.pack()
listbox_received_files = tk.Listbox(frame_received_files, width=50, height=10)
listbox_received_files.pack()

# 公共文件显示区域
frame_file_display = tk.Frame(tab_receive)
frame_file_display.pack(pady=10)
label_file_display = tk.Label(frame_file_display, text="文件显示:")
label_file_display.pack()
listbox_file_display = tk.Listbox(frame_file_display, width=50, height=10)
listbox_file_display.pack()

# 切换显示文件类型的按钮
frame_buttons = tk.Frame(tab_receive)
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

button_download = tk.Button(tab_receive, text="下载选中文件", command=download_file)
button_download.pack(pady=20)

# 运行主循环
root.mainloop()