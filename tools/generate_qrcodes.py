"""
二维码生成工具 - 每台机床生成 1 张二维码

使用方式：
    python tools/generate_qrcodes.py

生成结果保存在 qrcodes/ 目录下，每台机床 1 张：
    {machine_code}.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import qrcode
from config import BASE_URL, QR_DIR
from database.db import Database


def generate_single_qrcode(url: str, filename: str) -> str:
    """
    生成单张二维码图片。

    Args:
        url:      二维码内容（扫码后跳转的 URL）
        filename: 保存的文件名（含 .png 后缀）

    Returns:
        生成的二维码图片完整路径
    """
    os.makedirs(QR_DIR, exist_ok=True)
    filepath = os.path.join(QR_DIR, filename)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)

    return filepath


def generate_all_qrcodes() -> list[str]:
    """
    读取数据库中所有机床，每台生成 1 张二维码。

    Returns:
        所有生成的文件路径列表
    """
    db = Database()
    machines = db.execute(
        "SELECT id, machine_code, machine_name FROM machines ORDER BY machine_code"
    )

    if not machines:
        print("数据库中没有机床记录，请先启动 run.py 初始化数据库。")
        return []

    all_files = []
    print(f"\n共 {len(machines)} 台机床，每台生成 1 张二维码：\n")

    for m in machines:
        url = f"{BASE_URL}/mobile/?machine_id={m['id']}"
        filename = f"{m['machine_code']}.png"
        filepath = generate_single_qrcode(url, filename)
        all_files.append(filepath)
        print(f"  {m['machine_code']} ({m['machine_name']}) -> {filename}")

    print(f"\n全部生成完毕，共 {len(all_files)} 张图片。")
    print(f"保存目录: {os.path.abspath(QR_DIR)}\n")

    return all_files


if __name__ == "__main__":
    generate_all_qrcodes()
