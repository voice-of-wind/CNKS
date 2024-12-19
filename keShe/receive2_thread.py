import socket
import os
import threading


# 下载文件的部分
def download_part(file_path, server_ip, server_port, start_byte, end_byte, thread_id):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    # 获取文件大小
    file_size = int(client_socket.recv(1024).decode())
    print(f"文件大小: {file_size} bytes")

    # 告诉服务器线程数
    client_socket.send(str(4).encode())  # 假设使用4个线程

    # 向服务器请求下载的部分
    client_socket.send(str(start_byte).encode())
    client_socket.send(str(end_byte).encode())

    # 获取文件数据
    file_data = client_socket.recv(end_byte - start_byte)
    print(f"线程 {thread_id} 下载完成")

    # 保存文件数据到本地
    with open(file_path, 'r+b') as f:
        f.seek(start_byte)
        f.write(file_data)

    client_socket.close()


# 主函数：控制多线程下载
def download_file(file_path, server_ip, server_port, num_threads=4):
    # 获取文件的大小
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    file_size = int(client_socket.recv(1024).decode())
    print(f"文件大小: {file_size} bytes")

    # 创建一个空文件
    with open(file_path, 'wb') as f:
        f.truncate(file_size)

    # 每个线程负责的字节范围
    chunk_size = file_size // num_threads
    threads = []

    for i in range(num_threads):
        start_byte = i * chunk_size
        end_byte = start_byte + chunk_size if i < num_threads - 1 else file_size
        t = threading.Thread(target=download_part, args=(file_path, server_ip, server_port, start_byte, end_byte, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"文件 {file_path} 下载完成")


if __name__ == "__main__":
    file_path = '../res1/1.png'  # 目标保存路径
    server_ip = '127.0.0.1'  # 服务器IP
    server_port = 12345  # 服务器端口
    download_file(file_path, server_ip, server_port)
