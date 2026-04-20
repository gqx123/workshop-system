"""数据库建表语句"""

SCHEMA = """
-- ============================================================
-- 机床设备表
-- 存放车间所有机床的基本信息
-- ============================================================
CREATE TABLE IF NOT EXISTS machines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_code    TEXT    NOT NULL UNIQUE,                    -- 机床编号，如 MC-001
    machine_name    TEXT    NOT NULL,                           -- 机床名称，如 数控车床A
    machine_type    TEXT    NOT NULL DEFAULT '',                -- 机床类型，如 数控车床 / 铣床 / 磨床
    location        TEXT    NOT NULL DEFAULT '',                -- 所在位置，如 A区-1号位
    status          TEXT    NOT NULL DEFAULT '正常',             -- 当前状态：正常 / 停机 / 维修中
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ============================================================
-- 生产记录表
-- 每次开机生产填写一条记录
-- ============================================================
CREATE TABLE IF NOT EXISTS production_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id          INTEGER NOT NULL,                       -- 关联机床 ID
    product_name        TEXT    NOT NULL,                        -- 产品名称
    product_batch       TEXT    NOT NULL DEFAULT '',             -- 产品批次号
    plan_quantity       INTEGER NOT NULL DEFAULT 0,              -- 计划数量
    actual_quantity     INTEGER NOT NULL DEFAULT 0,              -- 实际完成数量
    defect_quantity     INTEGER NOT NULL DEFAULT 0,              -- 不良品数量
    start_time          TEXT    NOT NULL,                        -- 开始时间（yyyy-MM-dd HH:mm:ss）
    end_time            TEXT,                                    -- 结束时间（为空表示生产中）
    operator_name       TEXT    NOT NULL DEFAULT '',             -- 操作员姓名
    operator_id         TEXT    NOT NULL DEFAULT '',             -- 操作员工号
    remark              TEXT    NOT NULL DEFAULT '',             -- 备注
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- ============================================================
-- 保养记录表
-- 每次保养填写一条记录
-- ============================================================
CREATE TABLE IF NOT EXISTS maintenance_records (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id              INTEGER NOT NULL,                   -- 关联机床 ID
    maintenance_type        TEXT    NOT NULL,                    -- 保养类型：日常 / 周 / 月 / 季度 / 年度 / 临时维修
    description             TEXT    NOT NULL DEFAULT '',         -- 保养内容描述
    parts_replaced          TEXT    NOT NULL DEFAULT '',         -- 更换的零部件（逗号分隔或 JSON）
    next_maintenance_date   TEXT,                                -- 下次保养日期
    operator_name           TEXT    NOT NULL DEFAULT '',         -- 保养人姓名
    operator_id             TEXT    NOT NULL DEFAULT '',         -- 保养人工号
    duration_minutes        INTEGER NOT NULL DEFAULT 0,          -- 保养耗时（分钟）
    created_at              TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- ============================================================
-- 故障记录表
-- 每次发生故障填写一条记录
-- ============================================================
CREATE TABLE IF NOT EXISTS fault_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id      INTEGER NOT NULL,                           -- 关联机床 ID
    fault_type      TEXT    NOT NULL DEFAULT '',                 -- 故障类型
    description     TEXT    NOT NULL DEFAULT '',                 -- 故障描述
    severity        TEXT    NOT NULL DEFAULT '一般',              -- 故障等级：一般 / 严重 / 紧急
    status          TEXT    NOT NULL DEFAULT '待处理',            -- 处理状态：待处理 / 已解决
    operator_name   TEXT    NOT NULL DEFAULT '',                 -- 报告人姓名
    resolution      TEXT    NOT NULL DEFAULT '',                 -- 解决方案描述
    resolved_at     TEXT,                                        -- 解决时间
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- ============================================================
-- 点检模板表
-- 每台设备配置自己的点检项目列表
-- ============================================================
CREATE TABLE IF NOT EXISTS inspection_templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id      INTEGER NOT NULL,                           -- 关联机床 ID
    item_name       TEXT    NOT NULL,                            -- 点检项目名称，如"检查润滑油位"
    item_order      INTEGER NOT NULL DEFAULT 0,                  -- 排序序号
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- ============================================================
-- 点检记录表
-- 每次点检提交一条记录
-- ============================================================
CREATE TABLE IF NOT EXISTS inspection_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id      INTEGER NOT NULL,                           -- 关联机床 ID
    operator_name   TEXT    NOT NULL DEFAULT '',                 -- 点检人姓名
    remark          TEXT    NOT NULL DEFAULT '',                 -- 总备注
    details         TEXT    NOT NULL DEFAULT '[]',               -- 点检明细 JSON
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- ============================================================
-- 索引：加速常见查询
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_production_machine   ON production_records(machine_id);
CREATE INDEX IF NOT EXISTS idx_production_time      ON production_records(start_time);
CREATE INDEX IF NOT EXISTS idx_maintenance_machine  ON maintenance_records(machine_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_time     ON maintenance_records(created_at);
CREATE INDEX IF NOT EXISTS idx_fault_machine        ON fault_records(machine_id);
CREATE INDEX IF NOT EXISTS idx_fault_status         ON fault_records(status);
CREATE INDEX IF NOT EXISTS idx_fault_time           ON fault_records(created_at);
CREATE INDEX IF NOT EXISTS idx_insp_tpl_machine     ON inspection_templates(machine_id);
CREATE INDEX IF NOT EXISTS idx_insp_tpl_order       ON inspection_templates(machine_id, item_order);
CREATE INDEX IF NOT EXISTS idx_insp_rec_machine     ON inspection_records(machine_id);
CREATE INDEX IF NOT EXISTS idx_insp_rec_time        ON inspection_records(created_at);
"""
