import base64
import re

# 示例数据
data = b'3Qc8lnRM7EfwVGLgNPyLhJBtdFE/WwqcGSBcU/uNCAGHFtBqg==TALB\x00\x00\x00\x19\x00\x00\x01\xff\xfeP\x00r\x00a\x00y\x00'

# 使用正则表达式识别 Base64 编码部分
base64_pattern = re.compile(b'[A-Za-z0-9+/=]+')
base64_match = base64_pattern.match(data)

if base64_match:
    base64_data = base64_match.group(0)
    decoded_data = base64.b64decode(base64_data)
    print("Base64 解码后的数据:", decoded_data)
else:
    print("未找到 Base64 编码部分")

# 提取剩余的文本和二进制数据
remaining_data = data[len(base64_data):]
print("剩余的数据:", remaining_data)