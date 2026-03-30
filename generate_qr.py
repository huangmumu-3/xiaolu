#!/usr/bin/env python3
"""
生成小陆的专属二维码
"""
import qrcode
import os

# 这里填写你的服务器地址
# 本地测试用 localhost，外网访问需要公网IP或域名
SERVER_URL = "http://localhost:8080/chat"

# 生成二维码
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(SERVER_URL)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save("./QR.png")

print(f"✅ 二维码已生成: {os.path.abspath('./QR.png')}")
print(f"📱 扫描后访问: {SERVER_URL}")
