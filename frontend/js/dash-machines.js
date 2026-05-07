var DashMachines = (function () {
    'use strict';

    var tableBody = document.getElementById('machineTableBody');
    var loadingEl = document.getElementById('machineLoading');
    var emptyEl = document.getElementById('machineEmpty');
    var selectAllCb = document.getElementById('machineSelectAll');
    var exportBtn = document.getElementById('exportQrcodesBtn');
    var allMachines = [];

    // 二维码弹窗
    var qrModal = document.getElementById('qrcodeModal');
    var qrTitle = document.getElementById('qrcodeModalTitle');
    var qrClose = document.getElementById('qrcodeModalClose');
    var qrLoading = document.getElementById('qrcodeLoading');
    var qrContent = document.getElementById('qrcodeContent');
    var qrImg = document.getElementById('qrcodeImg');
    var qrInfo = document.getElementById('qrcodeMachineInfo');
    var qrDownload = document.getElementById('qrcodeDownloadBtn');

    function init() {
        // 全选/反选
        selectAllCb.addEventListener('change', function () {
            var checkboxes = tableBody.querySelectorAll('.machine-cb');
            for (var i = 0; i < checkboxes.length; i++) {
                checkboxes[i].checked = selectAllCb.checked;
            }
            updateExportBtn();
        });

        // 二维码弹窗关闭
        qrClose.addEventListener('click', closeQrcodeModal);
        qrModal.addEventListener('click', function (e) {
            if (e.target === qrModal) closeQrcodeModal();
        });
    }

    async function refresh() {
        showLoading(true);
        emptyEl.style.display = 'none';
        selectAllCb.checked = false;
        updateExportBtn();
        try {
            var machines = await API.machines.getAll();
            allMachines = machines;
            renderTable(machines);
            if (!machines.length) emptyEl.style.display = 'flex';
        } catch (err) {
            window.showToast('加载失败: ' + err.message, 'error');
        } finally {
            showLoading(false);
        }
    }

    function renderTable(machines) {
        var countEl = document.getElementById('machineCountMachines');
        if (countEl) countEl.textContent = '共 ' + machines.length + ' 台';
        var rows = '';
        for (var i = 0; i < machines.length; i++) {
            var m = machines[i];
            var mobileUrl = '/mobile/?machine_id=' + m.id;
            rows += '<tr>';
            rows += '<td><input type="checkbox" class="machine-cb" value="' + m.id + '" onchange="DashMachines.onCheckboxChange()"></td>';
            rows += '<td class="mono">' + esc(m.machine_code) + '</td>';
            rows += '<td>' + esc(m.machine_name) + '</td>';
            rows += '<td>' + esc(m.machine_type || '-') + '</td>';
            rows += '<td>' + esc(m.location || '-') + '</td>';
            rows += '<td>' + statusTag(m.status) + '</td>';
            rows += '<td>' + esc(m.operator_name || '-') + '</td>';
            rows += '<td style="white-space:nowrap;">';
            rows += '<a href="' + mobileUrl + '" target="_blank" style="font-size:12px;margin-right:8px;">扫码页</a>';
            rows += '<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;margin-right:4px;" onclick="DashMachines.openTplModal(' + m.id + ',\'' + escAttr(m.machine_code) + '\')">点检模板</button>';
            rows += '<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;margin-right:4px;" onclick="DashMachines.openEditModal(' + m.id + ')">编辑</button>';
            rows += '<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;margin-right:4px;" onclick="DashMachines.openQrcodeModal(' + m.id + ')">二维码</button>';
            rows += '<button class="btn btn-danger" style="padding:3px 10px;font-size:12px;" onclick="DashMachines.confirmDelete(' + m.id + ',\'' + escAttr(m.machine_code) + '\')">删除</button>';
            rows += '</td>';
            rows += '</tr>';
        }
        tableBody.innerHTML = rows;
    }

    // ---- 复选框变化 ----
    function onCheckboxChange() {
        var checkboxes = tableBody.querySelectorAll('.machine-cb');
        var allChecked = checkboxes.length > 0;
        for (var i = 0; i < checkboxes.length; i++) {
            if (!checkboxes[i].checked) { allChecked = false; break; }
        }
        selectAllCb.checked = allChecked;
        updateExportBtn();
    }

    function getSelectedIds() {
        var checkboxes = tableBody.querySelectorAll('.machine-cb:checked');
        var ids = [];
        for (var i = 0; i < checkboxes.length; i++) {
            ids.push(parseInt(checkboxes[i].value, 10));
        }
        return ids;
    }

    function updateExportBtn() {
        var ids = getSelectedIds();
        exportBtn.style.display = ids.length > 0 ? 'inline-flex' : 'none';
        if (ids.length > 0) {
            exportBtn.textContent = '导出选中二维码 (' + ids.length + ')';
        }
    }

    // ---- 二维码弹窗 ----
    function openQrcodeModal(id) {
        var machine = null;
        for (var i = 0; i < allMachines.length; i++) {
            if (allMachines[i].id === id) { machine = allMachines[i]; break; }
        }
        qrTitle.textContent = '设备二维码';
        qrInfo.textContent = machine ? (machine.machine_code + ' ' + machine.machine_name) : '';
        qrImg.src = '';
        qrLoading.style.display = 'flex';
        qrContent.style.display = 'none';
        qrModal.classList.add('open');

        // 加载图片
        var url = API.baseUrl + '/api/machines/' + id + '/qrcode';
        var img = new Image();
        img.onload = function () {
            qrImg.src = url;
            qrDownload.href = url;
            qrDownload.download = (machine ? machine.machine_code : 'qrcode') + '.png';
            qrLoading.style.display = 'none';
            qrContent.style.display = 'block';
        };
        img.onerror = function () {
            qrLoading.innerHTML = '<div style="color:var(--red);font-size:13px;">加载失败</div>';
        };
        img.src = url;
    }

    function closeQrcodeModal() {
        qrModal.classList.remove('open');
        qrImg.src = '';
    }

    // ---- 批量导出 ----
    async function exportSelectedQrcodes() {
        var ids = getSelectedIds();
        if (!ids.length) {
            window.showToast('请先勾选要导出的机床', 'warning');
            return;
        }

        exportBtn.disabled = true;
        exportBtn.textContent = '导出中...';

        try {
            var res = await fetch(API.baseUrl + '/api/machines/qrcodes/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ machine_ids: ids }),
            });

            if (!res.ok) {
                var err = await res.json().catch(function () { return {}; });
                throw new Error(err.error || '导出失败');
            }

            var blob = await res.blob();
            var a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'machine_qrcodes.zip';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(a.href);
            window.showToast('已导出 ' + ids.length + ' 台机床二维码', 'success');
        } catch (err) {
            window.showToast('导出失败: ' + err.message, 'error');
        } finally {
            exportBtn.disabled = false;
            updateExportBtn();
        }
    }

    // ---- 点检模板 ----
    function openTplModal(machineId, machineCode) {
        window.TplModal.open(machineId, machineCode);
    }

    function openCreateModal() {
        var html = '';
        html += '<div class="form-group"><label class="form-label">机床编号 <span style="color:var(--red)">*</span></label>';
        html += '<input class="form-input" id="nc_code" placeholder="如 MC-006"></div>';
        html += '<div class="form-group"><label class="form-label">机床名称 <span style="color:var(--red)">*</span></label>';
        html += '<input class="form-input" id="nc_name" placeholder="如 数控车床C"></div>';
        html += '<div class="form-group"><label class="form-label">机床类型</label>';
        html += '<input class="form-input" id="nc_type" placeholder="如 数控车床"></div>';
        html += '<div class="form-group"><label class="form-label">位置</label>';
        html += '<input class="form-input" id="nc_loc" placeholder="如 A区-3号位"></div>';
        html += '<div class="form-group"><label class="form-label">操作人员</label>';
        html += '<input class="form-input" id="nc_operator" placeholder="机床负责人"></div>';
        html += '<div class="form-group"><label class="form-label">初始状态</label>';
        html += '<select class="form-select" id="nc_status">';
        html += '<option value="正常">正常</option>';
        html += '<option value="停机">停机</option>';
        html += '<option value="维修中">维修中</option>';
        html += '</select></div>';

        window.Modal.openEdit('新增机床', html, function (close) {
            var code = document.getElementById('nc_code').value.trim();
            var name = document.getElementById('nc_name').value.trim();
            if (!code) { window.showToast('请填写机床编号', 'warning'); document.getElementById('nc_code').focus(); return; }
            if (!name) { window.showToast('请填写机床名称', 'warning'); document.getElementById('nc_name').focus(); return; }
            API.machines.create({
                machine_code: code,
                machine_name: name,
                machine_type: document.getElementById('nc_type').value.trim(),
                location: document.getElementById('nc_loc').value.trim(),
                operator_name: document.getElementById('nc_operator').value.trim(),
                status: document.getElementById('nc_status').value,
            }).then(function (result) {
                window.showToast('新增成功！ID: ' + result.id, 'success');
                close();
                refresh();
            }).catch(function (err) {
                window.showToast('新增失败: ' + err.message, 'error');
            });
        });
    }

    function openEditModal(id) {
        API.machines.getById(id).then(function (m) {
            var html = '';
            html += '<div class="form-group"><label class="form-label">机床编号</label>';
            html += '<input class="form-input" id="edit_mc_code" value="' + escAttr(m.machine_code) + '"></div>';
            html += '<div class="form-group"><label class="form-label">机床名称</label>';
            html += '<input class="form-input" id="edit_mc_name" value="' + escAttr(m.machine_name) + '"></div>';
            html += '<div class="form-group"><label class="form-label">机床类型</label>';
            html += '<input class="form-input" id="edit_mc_type" value="' + escAttr(m.machine_type) + '"></div>';
            html += '<div class="form-group"><label class="form-label">位置</label>';
            html += '<input class="form-input" id="edit_mc_loc" value="' + escAttr(m.location) + '"></div>';
            html += '<div class="form-group"><label class="form-label">操作人员</label>';
            html += '<input class="form-input" id="edit_mc_operator" value="' + escAttr(m.operator_name || '') + '"></div>';
            html += '<div class="form-group"><label class="form-label">状态</label>';
            html += '<select class="form-select" id="edit_mc_status">';
            html += '<option value="正常"' + (m.status === '正常' ? ' selected' : '') + '>正常</option>';
            html += '<option value="停机"' + (m.status === '停机' ? ' selected' : '') + '>停机</option>';
            html += '<option value="维修中"' + (m.status === '维修中' ? ' selected' : '') + '>维修中</option>';
            html += '</select></div>';

            window.Modal.openEdit('编辑机床', html, function (close) {
                API.machines.update(id, {
                    machine_code: document.getElementById('edit_mc_code').value.trim(),
                    machine_name: document.getElementById('edit_mc_name').value.trim(),
                    machine_type: document.getElementById('edit_mc_type').value.trim(),
                    location: document.getElementById('edit_mc_loc').value.trim(),
                    operator_name: document.getElementById('edit_mc_operator').value.trim(),
                    status: document.getElementById('edit_mc_status').value,
                }).then(function () {
                    window.showToast('更新成功', 'success');
                    close();
                    refresh();
                }).catch(function (err) {
                    window.showToast('更新失败: ' + err.message, 'error');
                });
            });
        }).catch(function (err) {
            window.showToast('加载失败: ' + err.message, 'error');
        });
    }

    function confirmDelete(id, code) {
        window.Modal.openDelete('确定要删除机床 "' + code + '" 吗？如有关联记录将无法删除。', function (close) {
            API.machines.remove(id).then(function () {
                window.showToast('删除成功', 'success');
                close();
                refresh();
            }).catch(function (err) {
                window.showToast('删除失败: ' + err.message, 'error');
                close();
            });
        });
    }

    function statusTag(s) {
        var map = { '正常': 'tag-green', '停机': 'tag-yellow', '维修中': 'tag-red' };
        return '<span class="tag ' + (map[s] || 'tag-primary') + '">' + esc(s) + '</span>';
    }

    function showLoading(show) {
        loadingEl.style.display = show ? 'flex' : 'none';
        if (show) { tableBody.innerHTML = ''; emptyEl.style.display = 'none'; }
    }

    function esc(str) {
        var el = document.createElement('span');
        el.textContent = str == null ? '' : str;
        return el.innerHTML;
    }

    function escAttr(str) {
        return (str || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    return {
        init: init,
        refresh: refresh,
        openCreateModal: openCreateModal,
        openEditModal: openEditModal,
        openQrcodeModal: openQrcodeModal,
        openTplModal: openTplModal,
        confirmDelete: confirmDelete,
        onCheckboxChange: onCheckboxChange,
        exportSelectedQrcodes: exportSelectedQrcodes,
    };
})();
