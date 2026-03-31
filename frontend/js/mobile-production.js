/**
 * 移动端 - 生产记录提交页面逻辑
 * URL 格式: /mobile/production.html?machine_id=1
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

    // 收集数据
    var data = collectFormData();
    if (!data) return;

    // 禁用按钮
    submitBtn.disabled = true;
    submitBtn.textContent = '提交中...';

    try {
      var result = await API.production.create(data);
      showToast('提交成功！记录ID: ' + result.id, 'success');
      resetForm();
    } catch (err) {
      showToast('提交失败: ' + err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = '提交生产记录';
    }
  });

  /**
   * 收集表单数据为 JSON 对象
   * @returns {Object|null} 校验通过返回数据对象，否则返回 null
   */
  function collectFormData() {
    var operatorName = getValue('operator_name');
    var productName = getValue('product_name');
    var actualQuantity = getValue('actual_quantity');

    if (!operatorName) {
      showToast('请填写操作人员', 'warning');
      focusField('operator_name');
      return null;
    }
    if (!productName) {
      showToast('请填写产品名称', 'warning');
      focusField('product_name');
      return null;
    }
    if (actualQuantity === '') {
      showToast('请填写实际数量', 'warning');
      focusField('actual_quantity');
      return null;
    }

    var startTime = getValue('start_time');
    // 如果用户选了 datetime-local，转成 "YYYY-MM-DD HH:MM:SS" 格式
    if (startTime) {
      startTime = startTime.replace('T', ' ') + ':00';
    } else {
      // 默认当前时间
      startTime = formatNow();
    }

    var endTime = getValue('end_time');
    if (endTime) {
      endTime = endTime.replace('T', ' ') + ':00';
    }

    return {
      machine_id: machineId,
      operator_name: operatorName,
      operator_id: getValue('operator_id'),
      product_name: productName,
      product_batch: getValue('product_batch'),
      plan_quantity: parseInt(getValue('plan_quantity'), 10) || 0,
      actual_quantity: parseInt(actualQuantity, 10) || 0,
      defect_quantity: parseInt(getValue('defect_quantity'), 10) || 0,
      start_time: startTime,
      end_time: endTime || null,
      remark: getValue('remark'),
    };
  }

  // ----------------------------------------------------------------
  // 工具函数
  // ----------------------------------------------------------------

  /** 获取 input 值并 trim */
  function getValue(id) {
    return (document.getElementById(id).value || '').trim();
  }

  /** 聚焦到指定字段 */
  function focusField(id) {
    document.getElementById(id).focus();
  }

  /** 重置表单 */
  function resetForm() {
    form.reset();
    // 设置默认开始时间为当前时间
    document.getElementById('start_time').value = toDatetimeLocal(new Date());
  }

  /** 格式化当前时间为 "YYYY-MM-DD HH:MM:SS" */
  function formatNow() {
    var d = new Date();
    var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) +
      ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
  }

  /** Date 对象转 datetime-local 输入框格式 "YYYY-MM-DDTHH:MM" */
  function toDatetimeLocal(d) {
    var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) +
      'T' + pad(d.getHours()) + ':' + pad(d.getMinutes());
  }

  /** 显示 Toast 提示 */
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

  // ----------------------------------------------------------------
  // 初始化：设置默认开始时间为当前时间
  // ----------------------------------------------------------------
  document.getElementById('start_time').value = toDatetimeLocal(new Date());

})();
