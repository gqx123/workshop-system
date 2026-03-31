/**
 * 仪表盘 - 总览面板
 * 显示今日统计 + 各机床产量 + 待处理故障徽章
 */
var DashOverview = (function () {
  'use strict';

  var statsEl = document.getElementById('overviewStats');
  var machinesEl = document.getElementById('overviewMachines');
  var faultBadge = document.getElementById('faultBadge');

  // ----------------------------------------------------------------
  // 初始化
  // ----------------------------------------------------------------
  function init() {
    refresh();
  }

  // ----------------------------------------------------------------
  // 刷新数据
  // ----------------------------------------------------------------
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

  // ----------------------------------------------------------------
  // 渲染统计卡片
  // ----------------------------------------------------------------
  function renderStats(data) {
    var today = data.today || {};
    var cards = [
      {
        label: '今日生产记录',
        value: today.records || 0,
        sub: '条记录',
        cls: 'stat-primary',
      },
      {
        label: '今日总产量',
        value: today.total_quantity || 0,
        sub: '件',
        cls: 'stat-green',
      },
      {
        label: '今日不良品',
        value: today.total_defects || 0,
        sub: '件',
        cls: (today.total_defects || 0) > 0 ? 'stat-red' : '',
      },
      {
        label: '待处理故障',
        value: data.pending_faults || 0,
        sub: '条待处理',
        cls: (data.pending_faults || 0) > 0 ? 'stat-yellow' : '',
      },
    ];

    statsEl.innerHTML = cards.map(function (c) {
      return (
        '<div class="stat-card ' + c.cls + '">' +
          '<div class="stat-label">' + c.label + '</div>' +
          '<div class="stat-value">' + c.value + '</div>' +
          '<div class="stat-sub">' + c.sub + '</div>' +
        '</div>'
      );
    }).join('');
  }

  // ----------------------------------------------------------------
  // 渲染机床今日产量卡片
  // ----------------------------------------------------------------
  function renderMachines(list) {
    if (!list.length) {
      machinesEl.innerHTML =
        '<div class="empty-state" style="grid-column:1/-1;">' +
          '<div class="empty-text">暂无机床数据</div>' +
        '</div>';
      return;
    }

    machinesEl.innerHTML = list.map(function (m) {
      var hasDefect = m.defects > 0;
      return (
        '<div class="machine-card">' +
          '<div class="mc-code">' + esc(m.code) + '</div>' +
          '<div class="mc-name">' + esc(m.name) + '</div>' +
          '<div class="mc-meta">' +
            '产量: <strong>' + m.quantity + '</strong>' +
            (hasDefect
              ? ' &nbsp;|&nbsp; 不良: <strong style="color:var(--red)">' + m.defects + '</strong>'
              : '') +
          '</div>' +
        '</div>'
      );
    }).join('');
  }

  // ----------------------------------------------------------------
  // 更新侧边栏故障徽章
  // ----------------------------------------------------------------
  function updateBadge(count) {
    faultBadge.textContent = count;
    if (count > 0) {
      faultBadge.classList.add('visible');
    } else {
      faultBadge.classList.remove('visible');
    }
  }

  // ----------------------------------------------------------------
  // 工具
  // ----------------------------------------------------------------
  function esc(str) {
    var el = document.createElement('span');
    el.textContent = str;
    return el.innerHTML;
  }

  // ----------------------------------------------------------------
  // 暴露
  // ----------------------------------------------------------------
  return { init: init, refresh: refresh };

})();
