var DashOverview = (function () {
    var statsEl = document.getElementById('overviewStats');
    var machinesEl = document.getElementById('overviewMachines');
    var faultBadge = document.getElementById('faultBadge');
    var allMachineData = [];
    var currentFilter = 'all';

    function init() {
        refresh();
        var btns = document.querySelectorAll('.filter-btn');
        for (var i = 0; i < btns.length; i++) {
            btns[i].addEventListener('click', function () {
                for (var j = 0; j < btns.length; j++) {
                    btns[j].classList.remove('active');
                }
                this.classList.add('active');
                currentFilter = this.getAttribute('data-filter');
                renderMachines(allMachineData);
            });
        }
    }
    async function refresh() {
        try {
            var data = await API.stats.overview();
            renderStats(data);
            allMachineData = data.machine_today || [];
            renderMachines(allMachineData);
            faultBadge.textContent = data.pending_faults || 0;
            if ((data.pending_faults || 0) > 0) {
                faultBadge.classList.add('visible');
            } else {
                faultBadge.classList.remove('visible');
            }
        } catch (err) {
            console.error('总览数据加载失败:', err);
        }
    }

    function renderStats(data) {
        var today = data.today || {};
        var cards = [
            { label: '今日生产记录', value: today.records || 0, sub: '条记录', cls: 'stat-primary' },
            { label: '今日总产量', value: today.total_quantity || 0, sub: '件', cls: 'stat-green' },
            { label: '今日不良品', value: today.total_defects || 0, sub: '件', cls: (today.total_defects || 0) > 0 ? 'stat-red' : '' },
            { label: '待处理故障', value: data.pending_faults || 0, sub: '条待处理', cls: (data.pending_faults || 0) > 0 ? 'stat-yellow' : '' }
        ];
        var html = '';
        for (var i = 0; i < cards.length; i++) {
            var c = cards[i];
            html = html + '<div class="stat-card ' + c.cls + '">';
            html = html + '<div class="stat-label">' + c.label + '</div>';
            html = html + '<div class="stat-value">' + c.value + '</div>';
            html = html + '<div class="stat-sub">' + c.sub + '</div></div>';
        }
        statsEl.innerHTML = html;
    }
    function renderMachines(list) {
        var countEl = document.getElementById('machineCountOverview');
        if (countEl) countEl.textContent = '共 ' + list.length + ' 台';
        var filtered = [];
        for (var i = 0; i < list.length; i++) {
            var m = list[i];
            if (currentFilter === 'uninspected' && m.inspected) continue;
            if (currentFilter === 'abnormal' && (!m.inspected || m.abnormal_count === 0)) continue;
            filtered.push(m);
        }
        if (filtered.length === 0) {
            var msg = '暂无机床数据';
            if (currentFilter === 'uninspected') msg = '今日所有设备已点检';
            if (currentFilter === 'abnormal') msg = '今日无异常点检';
            machinesEl.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><div class="empty-text">' + msg + '</div></div>';
            return;
        }
        var html = '';
        for (var j = 0; j < filtered.length; j++) {
            var m = filtered[j];
            var hasDefect = m.defects > 0;
            var smap = { '正常': 'tag-green', '停机': 'tag-yellow', '维修中': 'tag-red' };
            var scls = smap[m.machine_status] || 'tag-primary';
            var insp = '';
            if (m.inspected) {
                if (m.abnormal_count > 0) {
                    insp = '<span class="tag tag-yellow" style="font-size:13px;padding:4px 10px;">' + m.abnormal_count + '项异常</span>';
                } else {
                    insp = '<span class="tag tag-green" style="font-size:13px;padding:4px 10px;">已点检</span>';
                }
                var ts = m.insp_time || '';
                if (ts.length > 16) ts = ts.substring(11, 16);
                insp = insp + ' <span style="font-size:13px;color:var(--text-muted);margin-left:4px;">' + esc(m.insp_operator) + ' ' + ts + '</span>';
            } else {
                insp = '<span class="tag tag-red" style="font-size:13px;padding:4px 10px;">未点检</span>';
            }
            html = html + '<div class="machine-card">';
            html = html + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">';
            html = html + '<span class="mc-code">' + esc(m.code) + '</span>';
            html = html + '<span class="tag ' + scls + '" style="font-size:12px;padding:3px 8px;">' + esc(m.machine_status) + '</span>';
            html = html + '</div>';
            html = html + '<div class="mc-name">' + esc(m.name) + '</div>';
            html = html + '<div class="mc-meta" style="margin-top:8px;">';
            html = html + '产量: <strong>' + m.quantity + '</strong>';
            if (hasDefect) {
                html = html + ' | 不良: <strong style="color:var(--red)">' + m.defects + '</strong>';
            }
            html = html + '</div>';
            html = html + '<div style="margin-top:8px;display:flex;align-items:center;">' + insp + '</div>';
            html = html + '</div>';
        }
        machinesEl.innerHTML = html;
    }

    function esc(str) {
        var el = document.createElement('span');
        el.textContent = str == null ? '' : str;
        return el.innerHTML;
    }

    return { init: init, refresh: refresh };
})();
