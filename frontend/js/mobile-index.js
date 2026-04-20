/**
 * 移动端 - 记录类型选择页
 * URL 格式: /mobile/?machine_id=1
 */
;(function () {
  'use strict';

  var params = new URLSearchParams(window.location.search);
  var machineId = parseInt(params.get('machine_id'), 10);

  if (!machineId || isNaN(machineId)) {
    showToast('缺少 machine_id 参数，请扫码正确二维码', 'error');
    return;
  }

  // 设置三个链接的 href
  document.getElementById('linkProduction').href =
    '/frontend/mobile/production.html?machine_id=' + machineId;
  document.getElementById('linkInspection').href =
    '/frontend/mobile/inspection.html?machine_id=' + machineId;
  document.getElementById('linkFault').href =
    '/frontend/mobile/fault.html?machine_id=' + machineId;

  // 加载机床信息
  loadMachineInfo();

  async function loadMachineInfo() {
    try {
      var machine = await API.machines.getById(machineId);
      document.getElementById('machineCode').textContent = machine.machine_code;
      document.getElementById('machineName').textContent = machine.machine_name;
      document.getElementById('machineInfo').style.display = 'flex';
    } catch (err) {
      showToast('加载机床信息失败: ' + err.message, 'error');
    }
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
      toast.addEventListener('animationend', function () { toast.remove(); });
    }, 2000);
  }

})();
