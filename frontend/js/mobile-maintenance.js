/**
 * 移动端 - 保养记录提交页面逻辑
 * URL 格式: /mobile/maintenance.html?machine_id=1
 */
;(function () {
  'use strict';

  // ----------------------------------------------------------------
  // DOM 引用
  // ----------------------------------------------------------------
  var form = document.getElementById('recordForm');
  var submitBtn = document.getElementById('submitBtn');
  var machineInfoEl = document.getElementById('machineInfo');
  var machineCodeEl = document.getElementById('machineCode');
  var machineNameEl = document.getElementById('machineName');

  // ----------------------------------------------------------------
  // 从 URL 获取 machine_id
  // ----------------------------------------------------------------
  var params = new URLSearchParams(window.location.search);
  var machineId = parseInt(params.get('machine_id'), 10);

  if (!machineId || isNaN(machineId)) {
    showToast('缺少 machine_id 参数，请扫码正确二维码', 'error');
    form.style.display = 'none';
    return;
  }

  // ----------------------------------------------------------------
  // 加载机床信息
  // ----------------------------------------------------------------
  loadMachineInfo();

  async function loadMachineInfo() {
    try {
      var machine = await API.machines.getById(machineId);
      machineCodeEl.textContent = machine.machine_code;
      machineNameEl.textContent = machine.machine_name;
      machineInfoEl.style.display = 'flex';
    } catch (err) {
      showToast('加载机床信息失败: ' + err.message, 'error');
    }
  }

  // ----------------------------------------------------------------
  // 表单提交
  // ----------------------------------------------------------------
  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    var data = collectFormData();
    if (!data) return;

    submitBtn.disabled = true;
    submitBtn.textContent = '提交中...';

    try {
      var result = await API.maintenance.create(data);
      showToast('提交成功！记录ID: ' + result.id, 'success');
      resetForm();
    } catch (err) {
      showToast('提交失败: ' + err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = '提交保养记录';
    }
  });

  /**
   * 收集表单数据为 JSON 对象
   * @returns {Object|null}
   */
  function collectFormData() {
    var operatorName = getValue('operator_name');
    var maintenanceType = getValue('maintenance_type');
    var description = getValue('description');

    if (!operatorName) {
      showToast('请填写操作人员', 'warning');
      focusField('operator_name');
      return null;
    }
    if (!maintenanceType) {
      showToast('请选择保养类型', 'warning');
      focusField('maintenance_type');
      return null;
    }
    if (!description) {
      showToast('请填写保养内容', 'warning');
      focusField('description');
      return null;
    }

    return {
      machine_id: machineId,
      operator_name: operatorName,
      operator_id: getValue('operator_id'),
      maintenance_type: maintenanceType,
      description: description,
      parts_replaced: getValue('parts_replaced'),
      duration_minutes: parseInt(getValue('duration_minutes'), 10) || 0,
      next_maintenance_date: getValue('next_maintenance_date') || null,
    };
  }

  // ----------------------------------------------------------------
  // 工具函数
  // ----------------------------------------------------------------

  function getValue(id) {
    return (document.getElementById(id).value || '').trim();
  }

  function focusField(id) {
    document.getElementById(id).focus();
  }

  function resetForm() {
    form.reset();
  }

  function showToast(message, type) {
    type = type || 'success';
    var container = document.getElementById('toastContainer');
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(function () {
      toast.classList.add('toast-out');
      toast.addEventListener('animationend', function () {
        toast.remove();
      });
    }, 2000);
  }

})();
