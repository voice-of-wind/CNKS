import socket
import os
import tkinter as tk
from tkinter import filedialog, ttk

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

        # 遍历文件列表 依次发送文件
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            # 发送文件标识符
            typeF = get_file_type(file_path)
            s.sendall((typeF + splitF))
            # 发送文件名
            s.sendall(file_name.encode('utf-8') + splitF)

            # 发送文件内容

            with open(file_path, 'rb') as f:
                while (chunk := f.read(1024)):
                    s.sendall(chunk)
            # 发送文件结束标识符
            s.sendall(endF)

            print(f"{file_name} 文件发送完成")

def send_file_udp(file_paths, host, port):
    buffer_size = int(1024)  # 缓冲区大小
    buffer = b''  # 缓冲区
    remainSize = int(1024)
    # 记录每个文件发送的长度
    size = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # 遍历文件列表 依次发送文件
        for file_path in file_paths:
            file_name = os.path.basename(file_path)

            # 发送文件标识符
            typeF = get_file_type(file_path)
            buffer += (typeF + splitF)+(file_name.encode('utf-8') + splitF)
            print(buffer)
            # s.sendto((typeF + splitF), (host, port))
            # # 发送文件名
            # s.sendto(file_name.encode('utf-8') + splitF, (host, port))

            # 发送文件内容
            remainSize = buffer_size-len(buffer)
            with open(file_path, 'rb') as f:
                while (chunk := f.read(remainSize)):
                    buffer += chunk

                    s.sendto(buffer, (host, port))
                    size += len(buffer)
                    buffer = b''
                    remainSize = buffer_size
                # 发送剩余的内容和结尾标识符
                if buffer:
                    s.sendto(buffer, (host, port))
                    remainSize = buffer_size
                    size += len(buffer)
                s.sendto(endF, (host, port))
                size += len(endF)
            print(f"{file_name} 文件发送完成  大小为{int(size/1024)}字节")
            size = 0

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

# 主机地址输入框
frame_host = tk.Frame(root)
frame_host.pack(pady=10)
label_host = tk.Label(frame_host, text="主机地址:")
label_host.pack(side=tk.LEFT)
entry_host = tk.Entry(frame_host, width=20)
entry_host.pack(side=tk.LEFT, padx=5)
entry_host.insert(0, "127.0.0.1")  # 设置默认值

# 端口号输入框
frame_port = tk.Frame(root)
frame_port.pack(pady=10)
label_port = tk.Label(frame_port, text="端口号:")
label_port.pack(side=tk.LEFT)
entry_port = tk.Entry(frame_port, width=10)
entry_port.pack(side=tk.LEFT, padx=5)
entry_port.insert(0, "12000")  # 设置默认值

# 协议选择下拉菜单
frame_protocol = tk.Frame(root)
frame_protocol.pack(pady=10)
label_protocol = tk.Label(frame_protocol, text="选择协议:")
label_protocol.pack(side=tk.LEFT)
protocol_var = tk.StringVar(value="UDP")
protocol_menu = ttk.Combobox(frame_protocol, textvariable=protocol_var, values=["TCP", "UDP"], state="readonly")
protocol_menu.pack(side=tk.LEFT, padx=5)

# 发送按钮
button_send = tk.Button(root, text="发送", command=send_files)
button_send.pack(pady=20)

# 运行主循环
root.mainloop()