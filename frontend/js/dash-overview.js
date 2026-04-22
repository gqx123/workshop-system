var DashOverview = (function () {
  'use strict';

  var statsEl = document.getElementById('overviewStats');
  var machinesEl = document.getElementById('overviewMachines');
  var faultBadge = document.getElementById('faultBadge');

  function init() {
    refresh();
  }

  async function refresh() {
    try {
      var data = await API.stats.overview();
      renderStats(data);
      renderMachines(data.machine_today || []);
      updateBadge(data.pending_faults || 0);
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
      { label: '待处理故障', value: data.pending_faults || 0, sub: '条待处理', cls: (data.pending_faults || 0) > 0 ? 'stat-yellow' : '' },
    ];

    var html = '';
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      html += '<div class="stat-card ' + c.cls + '">';
      html += '<div class="stat-label">' + c.label + '</div>';
      html += '<div class="stat-value">' + c.value + '</div>';
      html += '<div class="stat-sub">' + c.sub + '</div>';
      html += '</div>';
    }
    statsEl.innerHTML = html;
  }

  function renderMachines(list) {
    if (!list.length) {
      machinesEl.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><div class="empty-text">暂无机床数据</div></div>';
      return;
    }

    var html = '';
    for (var i = 0; i < list.length; i++) {
      var m = list[i];
      var hasDefect = m.defects > 0;

      // 机床状态颜色
      var statusMap = { '正常': 'tag-green', '停机': 'tag-yellow', '维修中': 'tag-red' };
      var statusCls = statusMap[m.machine_status] || 'tag-primary';

      // 点检状态
      var inspHtml = '';
      if (m.inspected) {
        var timeStr = m.insp_time || '';
        if (timeStr.length > 16) timeStr = timeStr.substring(11, 16);
        inspHtml = '<span class="tag tag-green" style="font-size:11px;">&#10003; 已点检</span>';
        inspHtml += ' <span style="font-size:11px;color:var(--text-muted);">' + esc(m.insp_operator) + ' ' + timeStr + '</span>';
      } else {
        inspHtml = '<span class="tag tag-red" style="font-size:11px;">&#10007; 未点检</span>';
      }

      html += '<div class="machine-card">';
      html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">';
      html += '<span class="mc-code">' + esc(m.code) + '</span>';
      html += '<span class="tag ' + statusCls + '" style="font-size:11px;">' + esc(m.machine_status) + '</span>';
      html += '</div>';
      html += '<div class="mc-name">' + esc(m.name) + '</div="margin-top:6px;">';
      html += '产量: <strong>' + m.quantity + '</strong>';
      if (hasDefect) {
        html += ' &nbsp;|&nbsp; 不良: <strong style="color:var(--red)">' + m.defects + '</strong>';
      }
      html += '</div>';
      html += '<div class="mc-meta" style="margin-top:6px;">' + inspHtml + '</div>';
      html += '</div>';
    }
    machinesEl.innerHTML = html;
  }

  function updateBadge(count) {
    faultBadge.textContent = count;
    if (count > 0) {
      faultBadge.classList.add('visible');
    } else {
      faultBadge.classList.remove('visible');
    }
  }

  function esc(str) {
    var el = document.createElement('span');
    el.textContent = str;
    return el.innerHTML;
  }

  return { init: init, refresh: refresh };
})();
