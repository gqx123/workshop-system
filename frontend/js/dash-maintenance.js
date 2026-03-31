/**
 * 仪表盘 - 保养记录面板（含编辑/删除）
 */
var DashMaintenance = (function () {
  'use strict';

  var tableBody = document.getElementById('maintTableBody');
  var loadingEl = document.getElementById('maintLoading');
  var emptyEl = document.getElementById('maintEmpty');
  var filterMachine = document.getElementById('maintFilterMachine');
  var filterBtn = document.getElementById('maintFilterBtn');

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
      var records = await API.maintenance.list(params);
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
          '<td class="mono">' + esc(r.created_at || '-') + '</td>' +
          '<td>' + esc(r.machine_code || '') + '</td>' +
          '<td><span class="tag tag-primary">' + esc(r.maintenance_type || '-') + '</span></td>' +
          '<td>' + truncate(esc(r.description || ''), 30) + '</td>' +
          '<td>' + esc(r.parts_replaced || '-') + '</td>' +
          '<td class="mono">' + (r.duration_minutes ? r.duration_minutes + '分钟' : '-') + '</td>' +
          '<td>' + esc(r.operator_name || '') + '</td>' +
          '<td class="mono">' + esc(r.next_maintenance_date || '-') + '</td>' +
          '<td style="white-space:nowrap;">' +
            '<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;margin-right:4px;" onclick="DashMaintenance.openEditModal(' + r.id + ')">编辑</button>' +
            '<button class="btn btn-danger" style="padding:3px 10px;font-size:12px;" onclick="DashMaintenance.confirmDelete(' + r.id + ')">删除</button>' +
          '</td>' +
        '</tr>'
      );
    }).join('');
  }

  function openEditModal(id) {
    API.maintenance.getById(id).then(function (r) {
      var html =
        '<div class="form-group"><label class="form-label">保养类型</label>' +
        '<select class="form-select" id="em_type">' +
          ['日常保养','周保养','月保养','季度保养','年度保养','临时维修'].map(function (t) {
            return '<option value="' + t + '"' + (r.maintenance_type === t ? ' selected' : '') + '>' + t + '</option>';
          }).join('') +
        '</select></div>' +
        '<div class="form-group"><label class="form-label">保养内容</label><textarea class="form-textarea" id="em_desc" rows="3">' + esc(r.description || '') + '</textarea></div>' +
        '<div class="form-group"><label class="form-label">更换部件</label><input class="form-input" id="em_parts" value="' + escAttr(r.parts_replaced) + '"></div>' +
        '<div class="form-row">' +
          '<div class="form-group"><label class="form-label">耗时(分钟)</label><input type="number" class="form-input" id="em_dur" value="' + (r.duration_minutes || 0) + '"></div>' +
          '<div class="form-group"><label class="form-label">操作人员</label><input class="form-input" id="em_op" value="' + escAttr(r.operator_name) + '"></div>' +
        '</div>' +
        '<div class="form-group"><label class="form-label">下次保养日期</label><input type="date" class="form-input" id="em_next" value="' + (r.next_maintenance_date || '') + '"></div>';

      window.Modal.openEdit('编辑保养记录', html, async function (close) {
        try {
          await API.maintenance.update(id, {
            maintenance_type: document.getElementById('em_type').value,
            description: document.getElementById('em_desc').value.trim(),
            parts_replaced: document.getElementById('em_parts').value.trim(),
            duration_minutes: parseInt(document.getElementById('em_dur').value, 10) || 0,
            operator_name: document.getElementById('em_op').value.trim(),
            next_maintenance_date: document.getElementById('em_next').value || null,
          });
          window.showToast('更新成功', 'success');
          close();
          refresh();
        } catch (err) { window.showToast('更新失败: ' + err.message, 'error'); }
      });
    }).catch(function (err) { window.showToast('加载失败: ' + err.message, 'error'); });
  }

  function confirmDelete(id) {
    window.Modal.openDelete('确定要删除这条保养记录吗？', async function (close) {
      try {
        await API.maintenance.remove(id);
        window.showToast('删除成功', 'success');
        close();
        refresh();
      } catch (err) { window.showToast('删除失败: ' + err.message, 'error'); close(); }
    });
  }

  function truncate(s, n) { return s && s.length > n ? s.substring(0, n) + '...' : (s || ''); }
  function showLoading(s) { loadingEl.style.display = s ? 'flex' : 'none'; if (s) { tableBody.innerHTML = ''; emptyEl.style.display = 'none'; } }
  function esc(s) { var e = document.createElement('span'); e.textContent = s == null ? '' : s; return e.innerHTML; }
  function escAttr(s) { return (s || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  return { init: init, refresh: refresh, openEditModal: openEditModal, confirmDelete: confirmDelete };
})();
