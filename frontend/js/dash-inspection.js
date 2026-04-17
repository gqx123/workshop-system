/**
 * 仪表盘 - 点检记录面板（查看 + 删除）
 */
var DashInspection = (function () {
  'use strict';

  var tableBody = document.getElementById('inspTableBody');
  var loadingEl = document.getElementById('inspLoading');
  var emptyEl = document.getElementById('inspEmpty');
  var filterMachine = document.getElementById('inspFilterMachine');
  var filterBtn = document.getElementById('inspFilterBtn');

  function init() {
    filterBtn.addEventListener('click', refresh);
    loadMachineOptions();
  }

  async function loadMachineOptions() {
    try {
      var machines = await API.machines.getAll();
      filterMachine.innerHTML = '<option value="">全部机床</option>' +
        machines.map(function (m) { return '<option value="' + m.id + '">' + esc(m.machine_code) + '</option>'; }).join('');
    } catch (e) { console.error(e); }
  }

  async function refresh() {
    showLoading(true);
    emptyEl.style.display = 'none';
    try {
      var params = {};
      var mid = filterMachine.value;
      if (mid) params.machine_id = mid;
      var records = await API.inspection.list(params);
      renderTable(records);
      if (!records.length) emptyEl.style.display = 'flex';
    } catch (err) {
      window.showToast('加载失败: ' + err.message, 'error');
    } finally {
      showLoading(false);
    }
  }

  function renderTable(records) {
    tableBody.innerHTML = records.map(function (r) {
      // 统计点检结果
      var details = r.details || [];
      var total = details.length;
      var abnormal = details.filter(function (d) { return d.result === '异常'; }).length;
      var resultHtml;
      if (total === 0) {
        resultHtml = '<span class="tag tag-primary">无明细</span>';
      } else if (abnormal === 0) {
        resultHtml = '<span class="tag tag-green">全部正常</span>';
      } else {
        resultHtml = '<span class="tag tag-red">' + abnormal + ' 项异常</span>';
      }

      return (
        '<tr>' +
          '<td class="mono">' + esc(r.created_at || '-') + '</td>' +
          '<td>' + esc(r.machine_code || '') + '</td>' +
          '<td>' + esc(r.operator_name || '') + '</td>' +
          '<td>' + resultHtml + '</td>' +
          '<td>' + truncate(esc(r.remark || ''), 20) + '</td>' +
          '<td style="white-space:nowrap;">' +
            '<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;margin-right:4px;" onclick="DashInspection.viewDetail(' + r.id + ')">详情</button>' +
            '<button class="btn btn-danger" style="padding:3px 10px;font-size:12px;" onclick="DashInspection.confirmDelete(' + r.id + ')">删除</button>' +
          '</td>' +
        '</tr>'
      );
    }).join('');
  }

  // ---- 查看详情 ----
  async function viewDetail(id) {
    try {
      var record = await API.inspection.getById(id);
      window.InspDetailModal.open(record);
    } catch (err) {
      window.showToast('加载失败: ' + err.message, 'error');
    }
  }

  // ---- 删除 ----
  function confirmDelete(id) {
    window.Modal.openDelete('确定要删除这条点检记录吗？', async function (close) {
      try {
        await API.inspection.remove(id);
        window.showToast('删除成功', 'success');
        close();
        refresh();
      } catch (err) {
        window.showToast('删除失败: ' + err.message, 'error');
        close();
      }
    });
  }

  // ---- 工具 ----
  function truncate(s, n) { return s && s.length > n ? s.substring(0, n) + '...' : (s || ''); }
  function showLoading(s) { loadingEl.style.display = s ? 'flex' : 'none'; if (s) { tableBody.innerHTML = ''; emptyEl.style.display = 'none'; } }
  function esc(s) { var e = document.createElement('span'); e.textContent = s == null ? '' : s; return e.innerHTML; }

  return { init: init, refresh: refresh, viewDetail: viewDetail, confirmDelete: confirmDelete };
})();
