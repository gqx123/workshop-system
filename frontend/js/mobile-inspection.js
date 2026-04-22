/**
 * 移动端 - 设备点检页面逻辑
 * URL 格式: /mobile/inspection.html?machine_id=1
 */
;(function () {
  'use strict';

  // ----------------------------------------------------------------
  // DOM 引用
  // ----------------------------------------------------------------
  var inspListEl = document.getElementById('inspList');
  var inspLoadingEl = document.getElementById('inspLoading');
  var inspFormEl = document.getElementById('inspForm');
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
    return;
  }

  // ----------------------------------------------------------------
  // 点检结果存储：{ templateId: { result: '正常'|'异常', note: '' } }
  // ----------------------------------------------------------------
  var inspResults = {};

  // ----------------------------------------------------------------
  // 加载机床信息 + 点检模板
  // ----------------------------------------------------------------
  loadMachineInfo();
  loadTemplates();

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

  async function loadTemplates() {
    try {
      var items = await API.inspectionTemplates.getAll(machineId);
      inspLoadingEl.style.display = 'none';
      if (!items.length) {
        inspListEl.innerHTML =
          '<div class="insp-empty">' +
            '<div style="font-size:36px;opacity:0.3;margin-bottom:8px;">&#9888;</div>' +
            '<div>该设备尚未配置点检模板</div>' +
            '<div style="font-size:12px;margin-top:4px;">请联系管理员在后台设置</div>' +
          '</div>';
        return;
      }
      renderItems(items);
      inspFormEl.style.display = 'block';
    } catch (err) {
      inspLoadingEl.style.display = 'none';
      showToast('加载点检项目失败: ' + err.message, 'error');
    }
  }

  // ----------------------------------------------------------------
  // 渲染点检项目列表
  // ----------------------------------------------------------------
  function renderItems(items) {
    var html = '';
    items.forEach(function (item, i) {
      var tid = item.id;
      // 默认全部为"正常"
      inspResults[tid] = { result: '正常', note: '' };

      html +=
        '<div class="insp-item" data-tid="' + tid + '" data-name="' + escAttr(item.item_name) + '">' +
          '<span class="insp-index">' + (i + 1) + '</span>' +
          '<span class="insp-name">' + esc(item.item_name) + '</span>' +
          '<div class="insp-toggle">' +
            '<button type="button" class="toggle-ok active-ok" data-tid="' + tid + '" onclick="setResult(' + tid + ',\'正常\',this)">正常</button>' +
            '<button type="button" class="toggle-bad" data-tid="' + tid + '" onclick="setResult(' + tid + ',\'异常\',this)">异常</button>' +
          '</div>' +
        '</div>' +
        '<div class="insp-note" id="note-' + tid + '" style="display:none;">' +
          '<input type="text" placeholder="请说明异常情况" oninput="setNote(' + tid + ', this.value)">' +
        '</div>';
    });
    inspListEl.innerHTML = html;
  }

  // ----------------------------------------------------------------
  // 切换正常/异常
  // ----------------------------------------------------------------
  window.setResult = function (tid, result, btnEl) {
    inspResults[tid].result = result;

    // 更新按钮样式
    var item = btnEl.closest('.insp-item');
    var okBtn = item.querySelector('.toggle-ok');
    var badBtn = item.querySelector('.toggle-bad');

    okBtn.classList.remove('active-ok');
    badBtn.classList.remove('active-bad');

    if (result === '正常') {
      okBtn.classList.add('active-ok');
    } else {
      badBtn.classList.add('active-bad');
    }

    // 显示/隐藏备注
    var noteEl = document.getElementById('note-' + tid);
    if (result === '异常') {
      noteEl.style.display = 'block';
      noteEl.querySelector('input').focus();
    } else {
      noteEl.style.display = 'none';
      noteEl.querySelector('input').value = '';
      inspResults[tid].note = '';
    }
  };

  // ----------------------------------------------------------------
  // 输入异常备注
  // ----------------------------------------------------------------
  window.setNote = function (tid, value) {
    inspResults[tid].note = value.trim();
  };

  // ----------------------------------------------------------------
  // 提交点检记录
  // ----------------------------------------------------------------
    submitBtn.addEventListener('click', async function () {
    var operatorName = (document.getElementById('operator_name').value || '').trim();
    if (!operatorName) {
      showToast('请填写点检人员', 'warning');
      document.getElementById('operator_name').focus();
      return;
    }

    // 构造 details 数组
    var details = [];
    var items = inspListEl.querySelectorAll('.insp-item');
    items.forEach(function (el) {
      var tid = parseInt(el.getAttribute('data-tid'), 10);
      var name = el.getAttribute('data-name');
      var r = inspResults[tid] || { result: '正常', note: '' };
      details.push({
        item_name: name,
        result: r.result,
        note: r.note,
      });
    });

    if (!details.length) {
      showToast('没有点检项目', 'warning');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = '提交中...';

    try {
      var result = await API.inspection.create({
        machine_id: machineId,
        operator_name: operatorName,
        remark: (document.getElementById('remark').value || '').trim(),
        details: details,
      });
      showToast('点检记录已提交！ID: ' + result.id, 'success');
      resetForm();
    } catch (err) {
      // 今日已点检的特殊处理
      if (err.message && err.message.indexOf('已点检') >= 0) {
        showToast('该设备今日已点检，不能重复提交。如需重新填写，请联系管理员删除今日记录后重试', 'error');
      } else {
        showToast('提交失败: ' + err.message, 'error');
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = '提交点检记录';
    }
  });

  // ----------------------------------------------------------------
  // 重置表单
  // ----------------------------------------------------------------
  function resetForm() {
    document.getElementById('operator_name').value = '';
    document.getElementById('remark').value = '';

    // 重置所有项目为正常
    var items = inspListEl.querySelectorAll('.insp-item');
    items.forEach(function (el) {
      var tid = parseInt(el.getAttribute('data-tid'), 10);
      inspResults[tid] = { result: '正常', note: '' };

      var okBtn = el.querySelector('.toggle-ok');
      var badBtn = el.querySelector('.toggle-bad');
      okBtn.classList.add('active-ok');
      badBtn.classList.remove('active-bad');

      var noteEl = document.getElementById('note-' + tid);
      noteEl.style.display = 'none';
      noteEl.querySelector('input').value = '';
    });
  }

  // ----------------------------------------------------------------
  // 工具函数
  // ----------------------------------------------------------------
  function esc(str) {
    var el = document.createElement('span');
    el.textContent = str == null ? '' : str;
    return el.innerHTML;
  }

  function escAttr(str) {
    return (str || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
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
