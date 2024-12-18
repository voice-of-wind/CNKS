import socket
import os
import tkinter as tk
from tkinter import messagebox, filedialog,ttk
import uuid

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
        vaildData = ""
        isFirst = True
        remainData = False
        with conn:
            while True:
                if not remainData:
                    data = conn.recv(1024)
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
                    datas = vaildData.split(splitF,2)
                    file_name = datas[1].decode('utf-8')
                    print(f"当前接收文件: {file_name}")
                    unique_id = uuid.uuid4()
                    file_name = str(unique_id) + "-" + file_name
                    save_path = os.path.join(f"../receive/{fileTypes[fileType]}", file_name)
                    fileData = datas[2]
                    dir_path = os.path.dirname(save_path)
                    if not os.path.exists(dir_path):
                        print("创建目录")
                        os.makedirs(dir_path)
                    # else:
                    fileType = -1
                    with open(save_path, 'wb') as f:
                        f.write(fileData)
                        while True:
                            # 如果文件头后面跟的有数据
                            chunk = conn.recv(1024)
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
                    save_paths.append(save_path)
                    file_names.append(file_name)
                    print(f"{file_name} 文件接收完成")
                else:
                    break
    print("接收完成")
    return save_paths, file_names

# 接收文件的函数（UDP）
def receive_file_udp(host, port):
    udpRecSize = int(1024)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((host, port))
        print("等待连接...")
        save_paths = []
        file_names = []

        while True:
            data, addr = s.recvfrom(udpRecSize)
            # 不要对数据进行utf-8解码，因为数据可能包含非utf-8字符 所以切割时 以及保存时 都不要解码
            print(f"发送文件的起始部分: {data}")
            print(f"收到数据的长度: {len(data)}")
            fileType = get_file_type(data)
            print(f"当前文件类型: {fileType}")
            # 如果接收到的数据为空，则退出循环
            if not data:
                break

            if fileType != -1:
                vaildData = data.split(beginFs[fileType])[1]
                datas = vaildData.split(splitF, 2)
                file_name = datas[1].decode('utf-8')
                print(f"当前接收文件: {file_name}")
                unique_id = uuid.uuid4()
                file_name = str(unique_id) + "-" + file_name
                save_path = os.path.join(f"../receive/{fileTypes[fileType]}", file_name)
                fileData = datas[2]
                dir_path = os.path.dirname(save_path)
                if not os.path.exists(dir_path):
                    print("创建目录")
                    os.makedirs(dir_path)
                fileType = -1
                with open(save_path, 'wb') as f:
                    f.write(fileData)
                    while True:
                        chunk, addr = s.recvfrom(udpRecSize)
                        # 文件尾是一个单独的标志位发送过来的
                        if endF in chunk:
                            print(f"最后一段数据: {chunk}")
                            break
                        else:
                            f.write(chunk)
                save_paths.append(save_path)
                file_names.append(file_name)
                print(f"{file_name} 文件接收完成")
            else:
                break
    print("接收完成")
    return save_paths, file_names


# 开始接收文件的函数
def start_receiving():
    host = entry_host_receive.get()
    port = int(entry_port_receive.get())
    protocol = protocol_var.get()
    if protocol == "TCP":
        save_paths, file_names = receive_file_tcp(host, port)
    elif protocol == "UDP":
        save_paths, file_names = receive_file_udp(host, port)
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

# region主机地址输入框
frame_host_receive = tk.Frame(root)
frame_host_receive.pack(pady=10)
label_host_receive = tk.Label(frame_host_receive, text="主机地址:")
label_host_receive.pack(side=tk.LEFT)
entry_host_receive = tk.Entry(frame_host_receive, width=20)
entry_host_receive.pack(side=tk.LEFT, padx=5)
entry_host_receive.insert(0, "127.0.0.1")
# endregion

# region端口号输入框
frame_port_receive = tk.Frame(root)
frame_port_receive.pack(pady=10)
label_port_receive = tk.Label(frame_port_receive, text="端口号:")
label_port_receive.pack(side=tk.LEFT)
entry_port_receive = tk.Entry(frame_port_receive, width=10)
entry_port_receive.pack(side=tk.LEFT, padx=5)
entry_port_receive.insert(0, "12000")
# endregion


# 协议选择下拉菜单
frame_protocol = tk.Frame(root)
frame_protocol.pack(pady=10)
label_protocol = tk.Label(frame_protocol, text="选择协议:")
label_protocol.pack(side=tk.LEFT)
protocol_var = tk.StringVar(value="UDP")
protocol_menu = ttk.Combobox(frame_protocol, textvariable=protocol_var, values=["TCP", "UDP"], state="readonly")
protocol_menu.pack(side=tk.LEFT, padx=5)


# region开始接收按钮
button_receive = tk.Button(root, text="开始接收", command=start_receiving)
button_receive.pack(pady=20)
# endregion

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

# 运行主循环
root.mainloop()
# endregion