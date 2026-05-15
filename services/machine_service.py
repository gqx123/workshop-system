"""机床业务逻辑层"""
import io
import os
import zipfile
import platform
import struct
from werkzeug.utils import secure_filename
from database.db import Database

db = Database()

INSTRUCTION_DIR_NAME = "instructions"


def get_all_machines() -> list[dict]:
    """获取所有机床列表，按编号升序"""
    return db.execute(
        "SELECT m.id, m.machine_code, m.machine_name, m.machine_type, "
        "m.location, m.status, m.operator_name, m.created_at, "
        "m.instruction_image, "
        "(SELECT COUNT(*) FROM inspection_templates t WHERE t.machine_id = m.id) AS tpl_count "
        "FROM machines m ORDER BY m.machine_code"
    )


def get_machine_by_id(machine_id: int) -> dict | None:
    """根据 ID 获取单台机床"""
    return db.execute_one(
        "SELECT id, machine_code, machine_name, machine_type, location, status, "
        "operator_name, instruction_image, created_at "
        "FROM machines WHERE id = ?",
        (machine_id,),
    )


def get_machine_by_code(code: str) -> dict | None:
    """根据编号获取单台机床"""
    return db.execute_one(
        "SELECT id, machine_code, machine_name, machine_type, location, status, "
        "operator_name, instruction_image, created_at "
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
    点检模板和作业指导书随机床一起清除，其他历史记录则阻止删除。
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

    # 清理作业指导书文件
    machine = get_machine_by_id(machine_id)
    if machine and machine.get("instruction_image"):
        _safe_delete_file(machine["instruction_image"], machine_id)

    # 点检模板随机床一起清除
    db.execute_write(
        "DELETE FROM inspection_templates WHERE machine_id = ?", (machine_id,)
    )

    rows = db.execute_write("DELETE FROM machines WHERE id = ?", (machine_id,))
    return rows > 0


# ================================================================
# 作业指导书
# ================================================================

def _get_instruction_dir() -> str:
    from config import UPLOAD_DIR
    path = os.path.join(UPLOAD_DIR, INSTRUCTION_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def _safe_delete_file(relative_path: str, exclude_machine_id: int | None = None):
    """
    删除文件，仅在无其他机床引用时才真正删磁盘文件。
    exclude_machine_id: 排除的机床 ID（即将被删除/覆盖的那台）
    """
    if exclude_machine_id:
        count = db.execute_one(
            "SELECT COUNT(*) AS cnt FROM machines WHERE instruction_image = ? AND id != ?",
            (relative_path, exclude_machine_id),
        )
    else:
        count = db.execute_one(
            "SELECT COUNT(*) AS cnt FROM machines WHERE instruction_image = ?",
            (relative_path,),
        )

    if count and count["cnt"] > 0:
        return  # 还有别的机床在用，不删

    from config import BASE_DIR
    full_path = os.path.join(BASE_DIR, relative_path)
    if os.path.exists(full_path):
        os.remove(full_path)


def upload_instruction_image(machine_id: int, file_storage) -> str:
    """上传作业指导书图片"""
    machine = get_machine_by_id(machine_id)
    if not machine:
        raise ValueError("机床不存在")

    instruction_dir = _get_instruction_dir()

    # 如果已有图片，检查引用计数后删除旧文件
    old_path = machine.get("instruction_image", "")
    if old_path:
        _safe_delete_file(old_path, machine_id)

    # 保存新文件
    ext = os.path.splitext(secure_filename(file_storage.filename))[1] or ".png"
    filename = f"machine_{machine_id}{ext}"
    filepath = os.path.join(instruction_dir, filename)
    file_storage.save(filepath)

    relative_path = f"uploads/{INSTRUCTION_DIR_NAME}/{filename}"
    db.execute_write(
        "UPDATE machines SET instruction_image = ? WHERE id = ?",
        (relative_path, machine_id),
    )
    return relative_path


def delete_instruction_image(machine_id: int) -> bool:
    """删除作业指导书（含引用计数）"""
    machine = get_machine_by_id(machine_id)
    if not machine:
        raise ValueError("机床不存在")

    old_path = machine.get("instruction_image", "")
    if not old_path:
        return False

    _safe_delete_file(old_path, machine_id)
    db.execute_write(
        "UPDATE machines SET instruction_image = '' WHERE id = ?", (machine_id,)
    )
    return True


def copy_instruction_image(source_id: int, target_id: int):
    """复制作业指导书引用（共享同一文件）"""
    if source_id == target_id:
        raise ValueError("源设备和目标设备不能相同")

    source = get_machine_by_id(source_id)
    if not source:
        raise ValueError("源设备不存在")
    source_path = source.get("instruction_image", "")
    if not source_path:
        raise ValueError("源设备没有作业指导书")

    target = get_machine_by_id(target_id)
    if not target:
        raise ValueError("目标设备不存在")

    # 删除目标设备旧文件（如有）
    old_target_path = target.get("instruction_image", "")
    if old_target_path:
        _safe_delete_file(old_target_path, target_id)

    db.execute_write(
        "UPDATE machines SET instruction_image = ? WHERE id = ?",
        (source_path, target_id),
    )


def get_instruction_image_path(machine_id: int) -> str | None:
    """获取作业指导书图片的完整路径，不存在返回 None"""
    machine = get_machine_by_id(machine_id)
    if not machine:
        return None

    relative_path = machine.get("instruction_image", "")
    if not relative_path:
        return None

    from config import BASE_DIR
    full_path = os.path.join(BASE_DIR, relative_path)
    if not os.path.exists(full_path):
        return None

    return full_path


# ================================================================
# 二维码生成
# ================================================================

def _find_chinese_font() -> str | None:
    """查找系统中可用的中文字体文件"""
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
    """生成带机床编号和名称的二维码卡片图片"""
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
    """批量生成二维码卡片，排版到 A4 PDF"""
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

    page_w, page_h = 210, 297
    cols, rows = 3, 4
    margin_x, margin_y = 5, 5
    cell_w = (page_w - 2 * margin_x) / cols
    cell_h = (page_h - 2 * margin_y) / rows
    card_print_w = 50

    pdf = FPDF(orientation="P", unit="mm", format="A4")

    for idx, m in enumerate(machines):
        pos = idx % (cols * rows)
        col = pos % cols
        row = pos // cols

        if pos == 0:
            pdf.add_page()
            pdf.set_draw_color(180, 180, 180)
            pdf.set_line_width(0.2)
            pdf.set_dash_pattern(dash=2, gap=2)
            for c in range(1, cols):
                lx = margin_x + c * cell_w
                pdf.line(lx, margin_y, lx, page_h - margin_y)
            for r in range(1, rows):
                ly = margin_y + r * cell_h
                pdf.line(margin_x, ly, page_w - margin_x, ly)
            pdf.set_dash_pattern()

        url = f"{BASE_URL}/mobile/?machine_id={m['id']}"
        card_png = _generate_qr_card(url, m["machine_code"], m["machine_name"])
        img_w, img_h = struct.unpack(">II", card_png[16:24])
        card_print_h = card_print_w * img_h / img_w
        cx = margin_x + col * cell_w + (cell_w - card_print_w) / 2
        cy = margin_y + row * cell_h + (cell_h - card_print_h) / 2
        pdf.image(io.BytesIO(card_png), x=cx, y=cy, w=card_print_w, h=card_print_h)

    return bytes(pdf.output())
