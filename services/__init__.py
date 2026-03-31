"""services 包初始化"""
from services.machine_service import (
    get_all_machines,
    get_machine_by_id,
    get_machine_by_code,
)
from services.production_service import (
    create_production,
    list_production,
    get_production_by_id,
)
from services.maintenance_service import (
    create_maintenance,
    list_maintenance,
)
from services.fault_service import (
    create_fault,
    list_faults,
    resolve_fault,
)
from services.stats_service import (
    get_overview_stats,
)

