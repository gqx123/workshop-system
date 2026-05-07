"""机床业务逻辑层"""
import io
import os
import platform
import struct
from database.db import Database

db = Database()


def get_all_machines() -> list[dict]:
    """获取所有机床列表，按编号升序"""
    return db.execute(
        "SELECT m.id, m.machine_code, m.machine_name, m.machine_type, "
        "m.location, m.status, m.operator_name, m.created_at, "
        "(SELECT COUNT(*) FROM inspection_templates t WHERE t.machine_id = m.id) AS tpl_count "
        "FROM machines m ORDER BY m.machine_code"
    )



def get_machine_by_id(machine_id: int) -> dict | None:
    """根据 ID 获取单台机床"""
    return db.execute_one(
        "SELECT id, machine_code, machine_name, machine_type, location, status, created_at "
        "FROM machines WHERE id = ?",
        (machine_id,),
    )


def get_machine_by_code(code: str) -> dict | None:
    """根据编号获取单台机床"""
    return db.execute_one(
        "SELECT id, machine_code, machine_name, machine_type, location, status, created_at "
        "FROM machines WHERE machine_code = ?",
        (code,),
    )


def create_machine(data):
    from database.db import DatabaseError
    required = ["machine_code", "machine_name"]
    for f in required:
        if f not in data or not data[f]:
            raise ValueError(f"缺少必填字段: {f}")

    try:
        db.execute_write(
            "INSERT INTO machines (machine_code, machine_name, machine_type, location, status, operator_name) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                data["machine_code"],
                data["machine_name"],
                data.get("machine_type", ""),
                data.get("location", ""),
                data.get("status", "正常"),
                data.get("operator_name", ""),
            ),
        )
    except DatabaseError as e:
        if "UNIQUE" in str(e) and "machine_code" in str(e):
            raise ValueError("保存失败，机床编号已存在")
        raise
    row = db.execute_one("SELECT last_insert_rowid() AS id")
    return row["id"]


def update_machine(machine_id, data):
    from database.db import DatabaseError
    allowed = {"machine_code", "machine_name", "machine_type", "location", "status", "operator_name"}
    updates, params = [], []
    for key, val in data.items():
        if key in allowed:
            updates.append(f"{key} = ?")
            params.append(val)
    if not updates:
        return False
    params.append(machine_id)
    try:
        rows = db.execute_write(
            f"UPDATE machines SET {', '.join(updates)} WHERE id = ?", tuple(params)
        )
    except DatabaseError as e:
        if "UNIQUE" in str(e) and "machine_code" in str(e):
            raise ValueError("保存失败，机床编号已存在")
        raise
    return rows > 0


def update_machine_status(machine_id: int, status: str) -> bool:
    """更新机床状态"""
    rows = db.execute_write(
        "UPDATE machines SET status = ? WHERE id = ?", (status, machine_id)
    )
    return rows > 0


def delete_machine(machine_id: int) -> bool:
    """
    删除机床。
    点检模板随机床一起清除，其他历史记录则阻止删除。
    """
    prod = db.execute_one(
        "SELECT COUNT(*) AS cnt FROM production_records WHERE machine_id = ?",
        (machine_id,),
    )
    if prod and prod["cnt"] > 0:
        raise ValueError("该机床存在生产记录，无法删除")

    maint = db.execute_one(
        "SELECT COUNT(*) AS cnt FROM maintenance_records WHERE machine_id = ?",
        (machine_id,),
    )
    if maint and maint["cnt"] > 0:
        raise ValueError("该机床存在保养记录，无法删除")

    fault = db.execute_one(
        "SELECT COUNT(*) AS cnt FROM fault_records WHERE machine_id = ?",
        (machine_id,),
    )
    if fault and fault["cnt"] > 0:
        raise ValueError("该机床存在故障记录，无法删除")

    insp = db.execute_one(
        "SELECT COUNT(*) AS cnt FROM inspection_records WHERE machine_id = ?",
        (machine_id,),
    )
    if insp and insp["cnt"] > 0:
        raise ValueError("该机床存在点检记录，无法删除")

    # 点检模板随机床一起清除
    db.execute_write(
        "DELETE FROM inspection_templates WHERE machine_id = ?", (machine_id,)
    )

    rows = db.execute_write("DELETE FROM machines WHERE id = ?", (machine_id,))
    return rows > 0


# ================================================================
# 二维码生成
# ================================================================

def _find_chinese_font() -> str | None:
    """查找系统中可用的中文字体文件，用于二维码卡片上的文字渲染"""
    candidates = []
    if platform.system() == "Windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        fonts = os.path.join(windir, "Fonts")
        candidates = [
            os.path.join(fonts, "msyh.ttc"),
            os.path.join(fonts, "msyhbd.ttc"),
            os.path.join(fonts, "simhei.ttf"),
            os.path.join(fonts, "simsun.ttc"),
        ]
    elif platform.system() == "Linux":
        candidates = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]
    elif platform.system() == "Darwin":
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
        ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def generate_qrcode_png(url: str) -> bytes:
    """根据 URL 生成纯二维码 PNG（用于弹窗预览）"""
    import qrcode

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def _generate_qr_card(url: str, code: str, name: str) -> bytes:
    """
    生成带机床编号和名称的二维码卡片图片。
    上半部分为二维码，下半部分为文字标注。
    """
    import qrcode
    from PIL import Image, ImageDraw, ImageFont

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_w, qr_h = qr_img.size

    # 文字区域高度（像素）
    text_area = 80
    card = Image.new("RGB", (qr_w, qr_h + text_area), "white")
    card.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(card)
    font_path = _find_chinese_font()
    try:
        font = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    text = f"{code} {name}"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (qr_w - tw) // 2
    ty = qr_h + (text_area - th) // 2
    draw.text((tx, ty), text, fill="black", font=font)

    buf = io.BytesIO()
    card.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def get_machine_qrcode(machine_id: int) -> tuple[bytes, str] | None:
    """生成单台机床的纯二维码 PNG（弹窗预览用）"""
    from config import BASE_URL

    machine = get_machine_by_id(machine_id)
    if not machine:
        return None
    url = f"{BASE_URL}/mobile/?machine_id={machine_id}"
    png = generate_qrcode_png(url)
    return png, f"{machine['machine_code']}.png"


def export_machines_qrcodes_pdf(machine_ids: list[int]) -> bytes | None:
    """
    批量生成二维码卡片，排版到 A4 PDF。
    布局：3 列 × 4 行 = 每页 12 个，含裁剪辅助线。
    """
    from config import BASE_URL
    from fpdf import FPDF

    if not machine_ids:
        return None

    placeholders = ",".join("?" * len(machine_ids))
    machines = db.execute(
        f"SELECT id, machine_code, machine_name FROM machines WHERE id IN ({placeholders})",
        tuple(machine_ids),
    )
    if not machines:
        return None

    # A4 页面参数（mm）
    page_w, page_h = 210, 297
    cols, rows = 3, 4
    margin_x, margin_y = 5, 5
    cell_w = (page_w - 2 * margin_x) / cols   # ≈66.67mm
    cell_h = (page_h - 2 * margin_y) / rows    # ≈71.75mm
    card_print_w = 50  # 二维码卡片打印宽度 5cm

    pdf = FPDF(orientation="P", unit="mm", format="A4")

    for idx, m in enumerate(machines):
        pos = idx % (cols * rows)
        col = pos % cols
        row = pos // cols

        # 每页开头：画裁剪辅助线
        if pos == 0:
            pdf.add_page()
            pdf.set_draw_color(180, 180, 180)
            pdf.set_line_width(0.2)
            pdf.set_dash_pattern(dash=2, gap=2)

            # 竖线
            for c in range(1, cols):
                lx = margin_x + c * cell_w
                pdf.line(lx, margin_y, lx, page_h - margin_y)
            # 横线
            for r in range(1, rows):
                ly = margin_y + r * cell_h
                pdf.line(margin_x, ly, page_w - margin_x, ly)

            pdf.set_dash_pattern()  # 恢复实线

        # 生成卡片图片
        url = f"{BASE_URL}/mobile/?machine_id={m['id']}"
        card_png = _generate_qr_card(url, m["machine_code"], m["machine_name"])

        # 从 PNG 头部读取图片尺寸，计算打印高度（保持比例）
        img_w, img_h = struct.unpack(">II", card_png[16:24])
        card_print_h = card_print_w * img_h / img_w

        # 居中放置在单元格内
        cx = margin_x + col * cell_w + (cell_w - card_print_w) / 2
        cy = margin_y + row * cell_h + (cell_h - card_print_h) / 2

        pdf.image(io.BytesIO(card_png), x=cx, y=cy, w=card_print_w, h=card_print_h)

    return bytes(pdf.output())
