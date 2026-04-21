"""机床业务逻辑层"""
from database.db import Database

db = Database()


def get_all_machines() -> list[dict]:
    """获取所有机床列表，按编号升序"""
    return db.execute(
        "SELECT id, machine_code, machine_name, machine_type, location, status, created_at "
        "FROM machines ORDER BY machine_code"
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
    required = ["machine_code", "machine_name"]
    for f in required:
        if f not in data or not data[f]:
            raise ValueError(f"缺少必填字段: {f}")

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
    row = db.execute_one("SELECT last_insert_rowid() AS id")
    return row["id"]


def update_machine(machine_id, data):
    allowed = {"machine_code", "machine_name", "machine_type", "location", "status", "operator_name"}
    updates, params = [], []
    for key, val in data.items():
        if key in allowed:
            updates.append(f"{key} = ?")
            params.append(val)
    if not updates:
        return False
    params.append(machine_id)
    rows = db.execute_write(
        f"UPDATE machines SET {', '.join(updates)} WHERE id = ?", tuple(params)
    )
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
    如果有关联记录则拒绝删除，返回 False。
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

    rows = db.execute_write("DELETE FROM machines WHERE id = ?", (machine_id,))
    return rows > 0
