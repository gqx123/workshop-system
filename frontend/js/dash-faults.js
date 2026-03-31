/**
 * 仪表盘 - 故障记录面板（含编辑/删除/解决）
 */
var DashFaults = (function () {
  'use strict';

  var tableBody = document.getElementById('faultTableBody');
  var loadingEl = document.getElementById('faultLoading');
  var emptyEl = document.getElementById('faultEmpty');
  var filterStatus = document.getElementById('faultFilterStatus');
  var filterBtn = document.getElementById('faultFilterBtn');

  // 解决弹窗
  var modal = document.getElementById('resolveModal');
  var modalClose = document.getElementById('resolveModalClose');
  var cancelBtn = document.getElementById('resolveCancelBtn');
  var confirmBtn = document.getElementById('resolveConfirmBtn');
  var resolveInput = document.getElementById('resolveInput');
  var currentFaultId = null;

  function init() {
    filterBtn.addEventListener('click', refresh);
    modalClose.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    confirmBtn.addEventListener('click', confirmResolve);
    modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
  }

  async function refresh() {
    showLoading(true);
    emptyEl.style.display = 'none';
    try {
      var params = {};
      var s = filterStatus.value; if (s) params.status = s;
      var records = await API.faults.list(params);
      renderTable(records);
      if (!records.length) emptyEl.style.display = 'flex';
    } catch (err) {
      window.showToast('加载失败: ' + err.message, 'error');
    } finally { showLoading(false); }
  }

  function renderTable(records) {
    tableBody.innerHTML = records.map(function (r) {
      var isPending = r.status === '待处理';
      var actions = '';
      if (isPending) {
        actions =
          '<button class="btn btn-primary" style="padding:3px 8px;font-size:11px;margin-right:3px;" onclick="DashFaults.openResolve(' + r.id + ')">解决</button>' +
          '<button class="btn btn-ghost" style="padding:3px 8px;font-size:11px;margin-right:3px;" onclick="DashFaults.openEditModal(' + r.id + ')">编辑</button>' +
          '<button class="btn btn-danger" style="padding:3px 8px;font-size:11px;" onclick="DashFaults.confirmDelete(' + r.id + ')">删除</button>';
      } else {
        actions =
          '<button class="btn btn-ghost" style="padding:3px 8px;font-size:11px;margin-right:3px;" onclick="DashFaults.openEditModal(' + r.id + ')">编辑</button>' +
          '<button class="btn btn-danger" style="padding:3px 8px;font-size:11px;" onclick="DashFaults.confirmDelete(' + r.id + ')">删除</button>';
      }
      return (
        '<tr>' +
          '<td class="mono">' + esc(r.created_at || '-') + '</td>' +
          '<td>' + esc(r.machine_code || '') + '</td>' +
          '<td>' + esc(r.fault_type || '-') + '</td>' +
          '<td>' + severityTag(r.severity) + '</td>' +
          '<td>' + truncate(esc(r.description || ''), 25) + '</td>' +
          '<td>' + statusTag(r.status) + '</td>' +
          '<td>' + esc(r.operator_name || '') + '</td>' +
          '<td style="white-space:nowrap;">' + actions + '</td>' +
        '</tr>'
      );
    }).join('');
  }

  // ---- 编辑 ----
  function openEditModal(id) {
    API.faults.getById(id).then(function (r) {
      var html =
        '<div class="form-group"><label class="form-label">故障类型</label>' +
        '<select class="form-select" id="ef_type">' +
          ['机械故障','电气故障','精度异常','异响','漏油','其他'].map(function (t) {
            return '<option value="' + t + '"' + (r.fault_type === t ? ' selected' : '') + '>' + t + '</option>';
          }).join('') +
        '</select></div>' +
        '<div class="form-group"><label class="form-label">严重程度</label>' +
        '<select class="form-select" id="ef_severity">' +
          ['一般','严重','紧急'].map(function (t) {
            return '<option value="' + t + '"' + (r.severity === t ? ' selected' : '') + '>' + t + '</option>';
          }).join('') +
        '</select></div>' +
        '<div class="form-group"><label class="form-label">故障描述</label><textarea class="form-textarea" id="ef_desc" rows="3">' + esc(r.description || '') + '</textarea></div>' +
        '<div class="form-group"><label class="form-label">上报人员</label><input class="form-input" id="ef_op" value="' + escAttr(r.operator_name) + '"></div>';

      window.Modal.openEdit('编辑故障记录', html, async function (close) {
        try {
          await API.faults.update(id, {
            fault_type: document.getElementById('ef_type').value,
            severity: document.getElementById('ef_severity').value,
            description: document.getElementById('ef_desc').value.trim(),
            operator_name: document.getElementById('ef_op').value.trim(),
          });
          window.showToast('更新成功', 'success');
          close();
          refresh();
        } catch (err) { window.showToast('更新失败: ' + err.message, 'error'); }
      });
    }).catch(function (err) { window.showToast('加载失败: ' + err.message, 'error'); });
  }

  // ---- 解决弹窗（保留原有逻辑） ----
  function openResolve(faultId) {
    currentFaultId = faultId;
    resolveInput.value = '';
    modal.classList.add('open');
    setTimeout(function () { resolveInput.focus(); }, 200);
  }
  function closeModal() { modal.classList.remove('open'); currentFaultId = null; resolveInput.value = ''; }
  async function confirmResolve() {
    var text = resolveInput.value.trim();
    if (!text) { window.showToast('请填写解决方案', 'warning'); resolveInput.focus(); return; }
    if (!currentFaultId) return;
    confirmBtn.disabled = true; confirmBtn.textContent = '提交中...';
    try {
      await API.faults.resolve(currentFaultId, text);
      window.showToast('故障已解决', 'success');
      closeModal();
      refresh();
    } catch (err) { window.showToast('操作失败: ' + err.message, 'error'); }
    finally { confirmBtn.disabled = false; confirmBtn.textContent = '确认解决'; }
  }

  // ---- 删除 ----
  function confirmDelete(id) {
    window.Modal.openDelete('确定要删除这条故障记录吗？', async function (close) {
      try {
        await API.faults.remove(id);
        window.showToast('删除成功', 'success');
        close();
        refresh();
      } catch (err) { window.showToast('删除失败: ' + err.message, 'error'); close(); }
    });
  }

  // ---- 工具 ----
  function severityTag(s) {
    var map = { '一般': 'tag-green', '严重': 'tag-yellow', '紧急': 'tag-red' };
    return '<span class="tag ' + (map[s] || 'tag-primary') + '">' + esc(s) + '</span>';
  }
  function statusTag(s) {
    return s === '待处理'
      ? '<span class="tag tag-yellow">待处理</span>'
      : '<span class="tag tag-green">' + esc(s) + '</span>';
  }
  function truncate(s, n) { return s && s.length > n ? s.substring(0, n) + '...' : (s || ''); }
  function showLoading(s) { loadingEl.style.display = s ? 'flex' : 'none'; if (s) { tableBody.innerHTML = ''; emptyEl.style.display = 'none'; } }
  function esc(s) { var e = document.createElement('span'); e.textContent = s == null ? '' : s; return e.innerHTML; }
  function escAttr(s) { return (s || '').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  return { init: init, refresh: refresh, openResolve: openResolve, openEditModal: openEditModal, confirmDelete: confirmDelete };
})();
