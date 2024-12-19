import socket
import threading
import os


# 每个线程负责发送文件的一部分
def send_file_part(client_socket, file_path, start_byte, end_byte):
    try:
        with open(file_path, 'rb') as f:
            f.seek(start_byte)
            data = f.read(end_byte - start_byte)
            client_socket.sendall(data)
        print(f"已发送文件部分：{start_byte} 到 {end_byte}")
    except Exception as e:
        print(f"发送文件部分时出错: {e}")
    finally:
        client_socket.close()


# 处理客户端连接
def handle_client(client_socket, file_path):
    # 获取文件的大小
    file_size = os.path.getsize(file_path)

    # 发送文件的总大小给客户端
    client_socket.send(str(file_size).encode())

    # 获取客户端的线程数
    num_threads = int(client_socket.recv(1024).decode())

    # 计算每个线程负责的字节范围
    chunk_size = file_size // num_threads
    threads = []

    for i in range(num_threads):
        start_byte = i * chunk_size
        # 最后一个线程负责剩余的字节
        end_byte = start_byte + chunk_size if i < num_threads - 1 else file_size
        t = threading.Thread(target=send_file_part, args=(client_socket, file_path, start_byte, end_byte))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


# 启动TCP服务器
def start_server(host='0.0.0.0', port=12345, file_path='large_file.txt'):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"服务器启动，监听 {host}:{port}...")

    while True:
        client_socket, client_address = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, file_path)).start()


if __name__ == "__main__":
    filepath = "../res/1.png"
    start_server(file_path=filepath)
