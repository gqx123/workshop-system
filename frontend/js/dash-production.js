/**
 * 仪表盘 - 生产记录面板（含编辑/删除）
 */
var DashProduction = (function () {
  'use strict';

  var tableBody = document.getElementById('prodTableBody');
  var loadingEl = document.getElementById('prodLoading');
  var emptyEl = document.getElementById('prodEmpty');
  var filterMachine = document.getElementById('prodFilterMachine');
  var filterFrom = document.getElementById('prodFilterFrom');
  var filterTo = document.getElementById('prodFilterTo');
  var filterBtn = document.getElementById('prodFilterBtn');

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
      var mid = filterMachine.value; if (mid) params.machine_id = mid;
      var from = filterFrom.value; if (from) params.from = from;
      var to = filterTo.value; if (to) params.to = to;
      var records = await API.production.list(params);
      renderTable(records);
      if (!records.length) emptyEl.style.display = 'flex';
    } catch (err) {
      window.showToast('加载失败: ' + err.message, 'error');
    } finally { showLoading(false); }
  }

  function renderTable(records) {
    tableBody.innerHTML = records.map(function (r) {
      return (
        '<tr>' +
          '<td class="mono">' + esc(r.start_time || '-') + '</td>' +
          '<td>' + esc(r.machine_code || '') + '</td>' +
          '<td>' + esc(r.product_name || '') + '</td>' +
          '<td>' + esc(r.product_batch || '-') + '</td>' +
          '<td class="mono">' + (r.plan_quantity || 0) + '</td>' +
          '<td class="mono">' + (r.actual_quantity || 0) + '</td>' +
          '<td class="mono">' + (r.defect_quantity ? '<span style="color:var(--red);font-weight:600">' + r.defect_quantity + '</span>' : '0') + '</td>' +
          '<td>' + esc(r.operator_name || '') + '</td>' +
          '<td style="white-space:nowrap;">' +
            '<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;margin-right:4px;" onclick="DashProduction.openEditModal(' + r.id + ')">编辑</button>' +
            '<button class="btn btn-danger" style="padding:3px 10px;font-size:12px;" onclick="DashProduction.confirmDelete(' + r.id + ')">删除</button>' +
          '</td>' +
        '</tr>'
      );
    }).join('');
  }

  // ---- 编辑 ----
  function openEditModal(id) {
    API.production.getById(id).then(function (r) {
      var html =
        '<div class="form-row">' +
          '<div class="form-group"><label class="form-label">产品名称</label><input class="form-input" id="ep_name" value="' + escAttr(r.product_name) + '"></div>' +
          '<div class="form-group"><label class="form-label">批次号</label><input class="form-input" id="ep_batch" value="' + escAttr(r.product_batch) + '"></div>' +
        '</div>' +
        '<div class="form-row">' +
          '<div class="form-group"><label class="form-label">计划数量</label><input type="number" class="form-input" id="ep_plan" value="' + (r.plan_quantity || 0) + '"></div>' +
          '<div class="form-group"><label class="form-label">实际数量</label><input type="number" class="form-input" id="ep_actual" value="' + (r.actual_quantity || 0) + '"></div>' +
          '<div class="form-group"><label class="form-label">不良品</label><input type="number" class="form-input" id="ep_defect" value="' + (r.defect_quantity || 0) + '"></div>' +
        '</div>' +
        '<div class="form-group"><label class="form-label">操作人员</label><input class="form-input" id="ep_operator" value="' + escAttr(r.operator_name) + '"></div>' +
        '<div class="form-group"><label class="form-label">备注</label><textarea class="form-textarea" id="ep_remark" rows="2">' + esc(r.remark || '') + '</textarea></div>';

      window.Modal.openEdit('编辑生产记录', html, async function (close) {
        try {
          await API.production.update(id, {
            product_name: document.getElementById('ep_name').value.trim(),
            product_batch: document.getElementById('ep_batch').value.trim(),
            plan_quantity: parseInt(document.getElementById('ep_plan').value, 10) || 0,
            actual_quantity: parseInt(document.getElementById('ep_actual').value, 10) || 0,
            defect_quantity: parseInt(document.getElementById('ep_defect').value, 10) || 0,
            operator_name: document.getElementById('ep_operator').value.trim(),
            remark: document.getElementById('ep_remark').value.trim(),
          });
          window.showToast('更新成功', 'success');
          close();
          refresh();
        } catch (err) { window.showToast('更新失败: ' + err.message, 'error'); }
      });
    }).catch(function (err) { window.showToast('加载失败: ' + err.message, 'error'); });
  }

  // ---- 删除 ----
  function confirmDelete(id) {
    window.Modal.openDelete('确定要删除这条生产记录吗？', async function (close) {
      try {
        await API.production.remove(id);
        window.showToast('删除成功', 'success');
        close();
        refresh();
      } catch (err) { window.showToast('删除失败: ' + err.message, 'error'); close(); }
    });
  }

  function showLoading(s) { loadingEl.style.display = s ? 'flex' : 'none'; if (s) { tableBody.innerHTML = ''; emptyEl.style.display = 'none'; } }
  function esc(s) { var e = document.createElement('span'); e.textContent = s == null ? '' : s; return e.innerHTML; }
  function escAttr(s) { return (s || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  return { init: init, refresh: refresh, openEditModal: openEditModal, confirmDelete: confirmDelete };
})();
