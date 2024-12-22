import os

file1 = "../receive/img/2.png"
file2 = "../res/2.png"

size1 = os.path.getsize(file1)
size2 = os.path.getsize(file2)

print(f"图片1大小: {size1} 字节")
print(f"图片2大小: {size2} 字节")
print(f"数据差异: {size1 - size2} 字节")


def compare_binary(file1, file2):
    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        data1 = f1.read()
        data2 = f2.read()

    # 比较文件大小
    num = 0

    min_len = min(len(data1), len(data2))
    print(f"文件大小对比: 文件1={len(data1)} 字节, 文件2={len(data2)} 字节")

    # 检查差异
    for i in range(min_len):
        if data1[i] != data2[i]:
            num+=1
            # print(f"差异位置: 第 {i} 字节, 文件1={data1[i]}, 文件2={data2[i]}")
            bin1 =   hex(data1[i])[2:]
            bin2 =   hex(data2[i])[2:]
            print(f"差异位置: 第 {i} 字节, 文件1={bin1}, 文件2={bin2}")

    # 检查是否有额外数据丢失
    if len(data1) != len(data2):
        print("文件大小不同，部分数据丢失。")
        if len(data1) > len(data2):
            print(f"文件2缺少 {len(data1) - len(data2)} 字节，从第 {min_len} 字节开始。")

    print(f"总共有 {num} 个字节不同。")

if __name__ == "__main__":
    compare_binary(file1, file2)

