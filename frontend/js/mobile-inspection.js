/**
 * 移动端 - 设备点检页面逻辑（含拍照 + 历史弹窗）
 * URL 格式: /mobile/inspection.html?machine_id=1
 */
; (function () {
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

    // 历史弹窗
    var historyBtn = document.getElementById('historyBtn');
    var historyOverlay = document.getElementById('historyOverlay');
    var historyBackdrop = document.getElementById('historyBackdrop');
    var historyClose = document.getElementById('historyClose');
    var historyQueryBtn = document.getElementById('historyQueryBtn');
    var historyFrom = document.getElementById('historyFrom');
    var historyTo = document.getElementById('historyTo');
    var historyBody = document.getElementById('historyBody');

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
    // 点检结果存储
    // ----------------------------------------------------------------
    var inspResults = {};
    var templateRequiresPhoto = {};

    // ----------------------------------------------------------------
    // 初始化
    // ----------------------------------------------------------------
    loadMachineInfo();
    loadTemplates();
    setHistoryDefaultDates();

    document.getElementById('backBtn').href = '/mobile/?machine_id=' + machineId;

    historyBtn.addEventListener('click', openHistory);
    historyClose.addEventListener('click', closeHistory);
    historyBackdrop.addEventListener('click', closeHistory);
    historyQueryBtn.addEventListener('click', loadHistory);

    function setHistoryDefaultDates() {
        var today = new Date();
        var y = today.getFullYear();
        var m = String(today.getMonth() + 1).padStart(2, '0');
        var d = String(today.getDate()).padStart(2, '0');
        var dateStr = y + '-' + m + '-' + d;
        historyFrom.value = dateStr;
        historyTo.value = dateStr;
    }

    function openHistory() {
        historyOverlay.classList.add('open');
        loadHistory();
    }

    function closeHistory() {
        historyOverlay.classList.remove('open');
    }

    // ----------------------------------------------------------------
    // 加载机床信息 + 点检模板
    // ----------------------------------------------------------------
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
    // 渲染点检项目
    // ----------------------------------------------------------------
    function renderItems(items) {
        var html = '';
        items.forEach(function (item, i) {
            var tid = item.id;
            var rp = item.requires_photo ? true : false;
            templateRequiresPhoto[tid] = rp;
            inspResults[tid] = { result: '正常', note: '', photo: '' };

            html += '<div class="insp-card" data-tid="' + tid + '" data-name="' + escAttr(item.item_name) + '" data-requires-photo="' + (rp ? '1' : '0') + '">';

            // 头部：序号 + 名称 + 正常/异常
            html += '  <div class="insp-card-header">';
            html += '    <span class="insp-index">' + (i + 1) + '</span>';
            html += '    <span class="insp-name">' + esc(item.item_name) + '</span>';
            html += '    <div class="insp-toggle">';
            html += '      <button type="button" class="toggle-ok active-ok" onclick="setResult(' + tid + ',\'正常\',this)">正常</button>';
            html += '      <button type="button" class="toggle-bad" onclick="setResult(' + tid + ',\'异常\',this)">异常</button>';
            html += '    </div>';
            html += '  </div>';

            // 底部：备注 + 拍照
            html += '  <div class="insp-card-footer">';

            // 备注
            html += '    <div class="insp-note" id="note-' + tid + '" style="display:none;">';
            html += '      <input type="text" placeholder="请说明异常情况" oninput="setNote(' + tid + ', this.value)">';
            html += '    </div>';

            // 拍照
            if (rp) {
                html += '    <input type="file" accept="image/*" capture="environment" id="photoInput-' + tid + '" style="display:none;" onchange="handlePhotoSelect(this,' + tid + ')">';
                // 未拍照状态
                html += '    <div class="photo-row" id="photoBtnRow-' + tid + '">';
                html += '      <div class="photo-upload-btn" onclick="document.getElementById(\'photoInput-' + tid + '\').click()">点击拍照</div>';
                html += '    </div>';
                // 已拍照状态
                html += '    <div class="photo-preview-row" id="photoPreview-' + tid + '" style="display:none;">';
                html += '      <img id="photoThumb-' + tid + '" onclick="window.open(this.src)">';
                html += '      <span class="photo-ok">✓ 已拍照</span>';
                html += '      <button type="button" class="btn btn-ghost retake-btn" onclick="retakePhoto(' + tid + ')">重拍</button>';
                html += '    </div>';
            }

            html += '  </div>';
            html += '</div>';
        });
        inspListEl.innerHTML = html;
    }



    // ----------------------------------------------------------------
    // 切换正常/异常
    // ----------------------------------------------------------------
    window.setResult = function (tid, result, btnEl) {
        inspResults[tid].result = result;
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

    window.setNote = function (tid, value) {
        inspResults[tid].note = value.trim();
    };

    // ----------------------------------------------------------------
    // 拍照上传
    // ----------------------------------------------------------------
    window.handlePhotoSelect = async function (input, tid) {
        var file = input.files[0];
        if (!file) return;

        if (file.size > 20 * 1024 * 1024) {
            showToast('文件过大，最大 20MB', 'warning');
            input.value = '';
            return;
        }

        var btnRow = document.getElementById('photoBtnRow-' + tid);
        btnRow.querySelector('.photo-upload-btn').textContent = '上传中...';
        btnRow.querySelector('.photo-upload-btn').style.pointerEvents = 'none';

        var formData = new FormData();
        formData.append('file', file);
        formData.append('machine_id', machineId);

        try {
            var res = await fetch(API.baseUrl + '/api/inspection/upload-photo', {
                method: 'POST',
                body: formData,
            });
            if (!res.ok) {
                var err = await res.json().catch(function () { return {}; });
                throw new Error(err.error || '上传失败');
            }
            var data = await res.json();
            inspResults[tid].photo = data.filename;

            document.getElementById('photoThumb-' + tid).src = API.baseUrl + '/api/inspection-photos/' + data.filename + '?t=' + Date.now();
            document.getElementById('photoPreview-' + tid).style.display = 'flex';
            btnRow.style.display = 'none';

            showToast('照片已上传', 'success');
        } catch (err) {
            showToast('照片上传失败: ' + err.message, 'error');
            var btn = btnRow.querySelector('.photo-upload-btn');
            btn.textContent = '点击拍照';
            btn.style.pointerEvents = '';
            input.value = '';
        }
    };

    window.retakePhoto = function (tid) {
        inspResults[tid].photo = '';
        document.getElementById('photoPreview-' + tid).style.display = 'none';
        document.getElementById('photoInput-' + tid).value = '';
        var btnRow = document.getElementById('photoBtnRow-' + tid);
        btnRow.style.display = '';
        var btn = btnRow.querySelector('.photo-upload-btn');
        btn.textContent = '点击拍照';
        btn.style.pointerEvents = '';
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

        // 校验必填照片
        var inspItems = inspListEl.querySelectorAll('.insp-card');
        for (var i = 0; i < inspItems.length; i++) {
            var tid = parseInt(inspItems[i].getAttribute('data-tid'), 10);
            var rp = inspItems[i].getAttribute('data-requires-photo') === '1';
            if (rp && (!inspResults[tid] || !inspResults[tid].photo)) {
                showToast('请完成所有需要拍照的点检项目', 'warning');
                return;
            }
        }

        var details = [];
        inspItems.forEach(function (el) {
            var tid = parseInt(el.getAttribute('data-tid'), 10);
            var name = el.getAttribute('data-name');
            var r = inspResults[tid] || { result: '正常', note: '', photo: '' };
            var item = { item_name: name, result: r.result, note: r.note };
            if (r.photo) item.photo = r.photo;
            details.push(item);
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
    // 历史记录
    // ----------------------------------------------------------------
    async function loadHistory() {
        historyBody.innerHTML =
            '<div class="loading" style="padding:32px 0;"><div class="loading-spinner"></div><span>加载中...</span></div>';

        try {
            var queryParams = { machine_id: machineId };
            var from = historyFrom.value;
            var to = historyTo.value;
            if (from) queryParams.from = from + ' 00:00:00';
            if (to) queryParams.to = to + ' 23:59:59';

            var records = await API.inspection.list(queryParams);

            if (!records.length) {
                historyBody.innerHTML =
                    '<div class="empty-state" style="padding:40px 0;"><div class="empty-text">该时间段内无点检记录</div></div>';
                return;
            }
            renderHistory(records);
        } catch (err) {
            historyBody.innerHTML =
                '<div style="padding:24px;text-align:center;color:var(--red);font-size:13px;">加载失败: ' + esc(err.message) + '</div>';
        }
    }

    function renderHistory(records) {
        var html = '';
        for (var i = 0; i < records.length; i++) {
            var r = records[i];
            var details = r.details || [];
            var total = details.length;
            var abnormal = 0;
            for (var j = 0; j < details.length; j++) {
                if (details[j].result === '异常') abnormal++;
            }

            var tagHtml;
            if (total === 0) {
                tagHtml = '<span class="tag tag-primary" style="font-size:12px;padding:2px 8px;">无明细</span>';
            } else if (abnormal === 0) {
                tagHtml = '<span class="tag tag-green" style="font-size:12px;padding:2px 8px;">全部正常</span>';
            } else {
                tagHtml = '<span class="tag tag-red" style="font-size:12px;padding:2px 8px;">' + abnormal + '项异常</span>';
            }

            var dateStr = r.created_at || '';
            if (dateStr.length > 16) dateStr = dateStr.substring(5, 16);

            html += '<div class="history-item">';
            html += '  <div class="hi-top" onclick="toggleHistoryDetail(this)">';
            html += '    <div class="hi-left">';
            html += '      <span class="hi-date">' + esc(dateStr) + '</span>';
            html += '      <span class="hi-operator">' + esc(r.operator_name || '-') + '</span>';
            html += '      ' + tagHtml;
            html += '    </div>';
            html += '    <span class="hi-arrow">&#8250;</span>';
            html += '  </div>';

            html += '  <div class="hi-detail">';
            for (var k = 0; k < details.length; k++) {
                var d = details[k];
                var dTagCls = d.result === '正常' ? 'tag-green' : 'tag-red';
                var noteHtml = d.note ? '<span class="hi-detail-note">(' + esc(d.note) + ')</span>' : '';
                var photoHtml = '';
                if (d.photo) {
                    photoHtml = '<img class="hi-detail-photo" src="' + API.baseUrl + '/api/inspection-photos/' + d.photo + '" onclick="window.open(this.src)" title="查看照片">';
                }
                html += '<div class="hi-detail-row">';
                html += '  <span class="hi-detail-name">' + esc(d.item_name) + '</span>';
                html += '  ' + noteHtml;
                html += '  ' + photoHtml;
                html += '  <span class="tag ' + dTagCls + '" style="font-size:12px;padding:2px 8px;">' + esc(d.result) + '</span>';
                html += '</div>';
            }
            if (r.remark) {
                html += '<div class="hi-remark">备注：' + esc(r.remark) + '</div>';
            }
            html += '  </div>';
            html += '</div>';
        }
        historyBody.innerHTML = html;
    }

    window.toggleHistoryDetail = function (el) {
        var item = el.closest('.history-item');
        item.classList.toggle('expanded');
    };

    // ----------------------------------------------------------------
    // 重置表单
    // ----------------------------------------------------------------
    function resetForm() {
        document.getElementById('operator_name').value = '';
        document.getElementById('remark').value = '';

        var items = inspListEl.querySelectorAll('.insp-card');
        items.forEach(function (el) {
            var tid = parseInt(el.getAttribute('data-tid'), 10);
            inspResults[tid] = { result: '正常', note: '', photo: '' };

            var okBtn = el.querySelector('.toggle-ok');
            var badBtn = el.querySelector('.toggle-bad');
            okBtn.classList.add('active-ok');
            badBtn.classList.remove('active-bad');

            var noteEl = document.getElementById('note-' + tid);
            noteEl.style.display = 'none';
            noteEl.querySelector('input').value = '';

            // 重置照片
            if (templateRequiresPhoto[tid]) {
                retakePhoto(tid);
            }
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
            toast.addEventListener('animationend', function () { toast.remove(); });
        }, 2000);
    }

})();
