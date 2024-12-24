import os

def generate_text_file(file_name, size_in_bytes):
    with open(file_name, 'w') as f:
        f.write('A' * size_in_bytes)

if __name__ == "__main__":
    file_name = "1024_bytes_file.txt"
    size_in_bytes = 1024
    generate_text_file(file_name, size_in_bytes)
    print(f"文件 {file_name} 已生成，大小为 {size_in_bytes} 字节")