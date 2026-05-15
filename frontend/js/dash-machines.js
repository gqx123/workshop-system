var DashMachines = (function () {
    'use strict';

    var tableBody = document.getElementById('machineTableBody');
    var loadingEl = document.getElementById('machineLoading');
    var emptyEl = document.getElementById('machineEmpty');

    // 批量模式 DOM
    var toolbarNormal = document.getElementById('machineToolbarNormal');
    var toolbarBatch = document.getElementById('machineToolbarBatch');
    var batchCountEl = document.getElementById('batchSelectedCount');
    var batchExportBtn = document.getElementById('batchExportBtn');
    var thCheckbox = document.getElementById('machineThCheckbox');
    var selectAllCb = document.getElementById('machineSelectAll');

    // 二维码弹窗 DOM
    var qrModal = document.getElementById('qrcodeModal');
    var qrTitle = document.getElementById('qrcodeModalTitle');
    var qrClose = document.getElementById('qrcodeModalClose');
    var qrLoading = document.getElementById('qrcodeLoading');
    var qrContent = document.getElementById('qrcodeContent');
    var qrImg = document.getElementById('qrcodeImg');
    var qrInfo = document.getElementById('qrcodeMachineInfo');
    var qrDownload = document.getElementById('qrcodeDownloadBtn');

    // 作业指导书弹窗 DOM
    var instrModal = document.getElementById('instrModal');
    var instrTitle = document.getElementById('instrModalTitle');
    var instrClose = document.getElementById('instrModalClose');
    var instrBody = document.getElementById('instrModalBody');

    var allMachines = [];
    var batchMode = false;

    function init() {
        // 二维码弹窗关闭
        qrClose.addEventListener('click', closeQrcodeModal);
        qrModal.addEventListener('click', function (e) {
            if (e.target === qrModal) closeQrcodeModal();
        });

        // 作业指导书弹窗关闭
        instrClose.addEventListener('click', closeInstrModal);
        instrModal.addEventListener('click', function (e) {
            if (e.target === instrModal) closeInstrModal();
        });

        // 全选/反选
        selectAllCb.addEventListener('change', function () {
            var cbs = tableBody.querySelectorAll('.machine-cb');
            for (var i = 0; i < cbs.length; i++) {
                cbs[i].checked = selectAllCb.checked;
            }
            updateBatchCount();
        });
    }

    async function refresh() {
        showLoading(true);
        emptyEl.style.display = 'none';
        if (batchMode) exitBatchMode();
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
            if (batchMode) {
                rows += '<td><input type="checkbox" class="machine-cb" value="' + m.id + '" onchange="DashMachines.onCbChange()"></td>';
            }
            rows += '<td class="mono">' + esc(m.machine_code) + '</td>';
            rows += '<td>' + esc(m.machine_name);
            if (m.tpl_count === 0) {
                rows += ' <span class="tag tag-yellow" style="font-size:11px;padding:2px 6px;cursor:pointer;" onclick="DashMachines.openTplModal(' + m.id + ',\'' + escAttr(m.machine_code) + '\')">未配置点检模板</span>';
            }
            if (!m.instruction_image) {
                rows += ' <span class="tag tag-yellow" style="font-size:11px;padding:2px 6px;cursor:pointer;" onclick="DashMachines.openInstrModal(' + m.id + ')">未上传作业指导书</span>';
            }
            rows += '</td>';
            rows += '<td>' + esc(m.machine_type || '-') + '</td>';
            rows += '<td>' + esc(m.location || '-') + '</td>';
            rows += '<td>' + statusTag(m.status) + '</td>';
            rows += '<td>' + esc(m.operator_name || '-') + '</td>';
            rows += '<td style="white-space:nowrap;">';
            rows += '<a href="' + mobileUrl + '" target="_blank" style="font-size:12px;margin-right:8px;">扫码页</a>';
            rows += '<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;margin-right:4px;" onclick="DashMachines.openTplModal(' + m.id + ',\'' + escAttr(m.machine_code) + '\')">点检模板</button>';
            rows += '<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;margin-right:4px;" onclick="DashMachines.openInstrModal(' + m.id + ')">作业指导书</button>';
            rows += '<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;margin-right:4px;" onclick="DashMachines.openEditModal(' + m.id + ')">编辑</button>';
            rows += '<button class="btn btn-ghost" style="padding:3px 10px;font-size:12px;margin-right:4px;" onclick="DashMachines.openQrcodeModal(' + m.id + ')">二维码</button>';
            rows += '<button class="btn btn-danger" style="padding:3px 10px;font-size:12px;" onclick="DashMachines.confirmDelete(' + m.id + ',\'' + escAttr(m.machine_code) + '\')">删除</button>';
            rows += '</td>';
            rows += '</tr>';
        }
        tableBody.innerHTML = rows;
    }

    // ================================================================
    // 批量模式
    // ================================================================

    function enterBatchMode() {
        batchMode = true;
        toolbarNormal.style.display = 'none';
        toolbarBatch.style.display = 'flex';
        thCheckbox.style.display = '';
        selectAllCb.checked = false;
        updateBatchCount();
        renderTable(allMachines);
    }

    function exitBatchMode() {
        batchMode = false;
        toolbarNormal.style.display = 'flex';
        toolbarBatch.style.display = 'none';
        thCheckbox.style.display = 'none';
        selectAllCb.checked = false;
        renderTable(allMachines);
    }

    function onCbChange() {
        var cbs = tableBody.querySelectorAll('.machine-cb');
        var allChecked = cbs.length > 0;
        for (var i = 0; i < cbs.length; i++) {
            if (!cbs[i].checked) { allChecked = false; break; }
        }
        selectAllCb.checked = allChecked;
        updateBatchCount();
    }

    function updateBatchCount() {
        var ids = getSelectedIds();
        batchCountEl.textContent = '已选 ' + ids.length + ' 台';
        batchExportBtn.disabled = ids.length === 0;
    }

    function getSelectedIds() {
        var cbs = tableBody.querySelectorAll('.machine-cb:checked');
        var ids = [];
        for (var i = 0; i < cbs.length; i++) {
            ids.push(parseInt(cbs[i].value, 10));
        }
        return ids;
    }

    // ================================================================
    // 二维码弹窗
    // ================================================================

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

    // ================================================================
    // 作业指导书弹窗
    // ================================================================

    function openInstrModal(machineId) {
        var machine = null;
        for (var i = 0; i < allMachines.length; i++) {
            if (allMachines[i].id === machineId) { machine = allMachines[i]; break; }
        }
        instrTitle.textContent = '作业指导书 - ' + (machine ? machine.machine_code : '');
        instrModal.classList.add('open');
        renderInstrContent(machine);
    }

    function closeInstrModal() {
        instrModal.classList.remove('open');
    }

    function renderInstrContent(machine) {
        if (!machine) {
            instrBody.innerHTML = '<div style="color:var(--red);font-size:13px;">机床数据加载失败</div>';
            return;
        }

        var hasImage = machine.instruction_image && machine.instruction_image.length > 0;
        var html = '';

        if (hasImage) {
            html += '<div style="text-align:center;margin-bottom:16px;">';
            html += '<img src="' + API.baseUrl + '/api/machines/' + machine.id + '/instruction/image?t=' + Date.now() + '" ';
            html += 'style="max-width:100%;max-height:400px;border:1px solid var(--border);border-radius:var(--radius-sm);" alt="作业指导书">';
            html += '</div>';
            html += '<div style="display:flex;gap:8px;margin-bottom:16px;">';
            html += '<label class="btn btn-primary" style="cursor:pointer;">更换图片<input type="file" accept="image/*" style="display:none;" onchange="DashMachines.handleInstrUpload(this,' + machine.id + ')"></label>';
            html += '<button class="btn btn-danger" onclick="DashMachines.deleteInstr(' + machine.id + ')">删除图片</button>';
            html += '</div>';
        } else {
            html += '<div style="text-align:center;padding:24px 0 16px;">';
            html += '<div style="font-size:40px;opacity:0.3;margin-bottom:8px;">&#128196;</div>';
            html += '<div style="font-size:13px;color:var(--text-muted);margin-bottom:16px;">暂无作业指导书</div>';
            html += '<label class="btn btn-primary" style="cursor:pointer;">上传图片<input type="file" accept="image/*" style="display:none;" onchange="DashMachines.handleInstrUpload(this,' + machine.id + ')"></label>';
            html += '</div>';
        }

        // 从其他设备复制
        var hasInstrMachines = [];
        for (var i = 0; i < allMachines.length; i++) {
            if (allMachines[i].id !== machine.id && allMachines[i].instruction_image && allMachines[i].instruction_image.length > 0) {
                hasInstrMachines.push(allMachines[i]);
            }
        }

        if (hasInstrMachines.length > 0) {
            html += '<div style="border-top:1px solid var(--border);padding-top:16px;">';
            html += '<div style="display:flex;gap:8px;align-items:center;padding:12px;background:var(--surface-2);border-radius:var(--radius-sm);">';
            html += '<label style="font-size:12px;color:var(--text-muted);white-space:nowrap;">从其他设备复制：</label>';
            html += '<select class="form-select" id="instrCopySource" style="flex:1;padding:7px 10px;font-size:13px;">';
            html += '<option value="">请选择源设备</option>';
            for (var j = 0; j < hasInstrMachines.length; j++) {
                html += '<option value="' + hasInstrMachines[j].id + '">' + esc(hasInstrMachines[j].machine_code) + ' ' + esc(hasInstrMachines[j].machine_name) + '</option>';
            }
            html += '</select>';
            html += '<button class="btn btn-primary" style="padding:7px 14px;font-size:12px;" onclick="DashMachines.copyInstr(' + machine.id + ')">复制</button>';
            html += '</div>';
            html += '</div>';
        }

        instrBody.innerHTML = html;
    }

    async function handleInstrUpload(input, machineId) {
        var file = input.files[0];
        if (!file) return;

        if (file.size > 20 * 1024 * 1024) {
            window.showToast('文件过大，最大支持 20MB', 'warning');
            input.value = '';
            return;
        }

        var formData = new FormData();
        formData.append('file', file);

        try {
            var res = await fetch(API.baseUrl + '/api/machines/' + machineId + '/instruction', {
                method: 'POST',
                body: formData,
            });
            if (!res.ok) {
                var err = await res.json().catch(function () { return {}; });
                throw new Error(err.error || '上传失败');
            }
            window.showToast('上传成功', 'success');
            allMachines = await API.machines.getAll();
            var machine = null;
            for (var i = 0; i < allMachines.length; i++) {
                if (allMachines[i].id === machineId) { machine = allMachines[i]; break; }
            }
            renderInstrContent(machine);
            renderTable(allMachines);
        } catch (err) {
            window.showToast('上传失败: ' + err.message, 'error');
        }
        input.value = '';
    }

    async function deleteInstr(machineId) {
        if (!confirm('确定要删除该设备的作业指导书吗？')) return;
        try {
            var res = await fetch(API.baseUrl + '/api/machines/' + machineId + '/instruction', { method: 'DELETE' });
            if (!res.ok) {
                var err = await res.json().catch(function () { return {}; });
                throw new Error(err.error || '删除失败');
            }
            window.showToast('删除成功', 'success');
            allMachines = await API.machines.getAll();
            var machine = null;
            for (var i = 0; i < allMachines.length; i++) {
                if (allMachines[i].id === machineId) { machine = allMachines[i]; break; }
            }
            renderInstrContent(machine);
            renderTable(allMachines);
        } catch (err) {
            window.showToast('删除失败: ' + err.message, 'error');
        }
    }

    async function copyInstr(targetMachineId) {
        var sourceSelect = document.getElementById('instrCopySource');
        var sourceId = parseInt(sourceSelect.value, 10);
        if (!sourceId) {
            window.showToast('请选择源设备', 'warning');
            return;
        }
        try {
            var res = await fetch(API.baseUrl + '/api/machines/instruction/copy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_machine_id: sourceId, target_machine_id: targetMachineId }),
            });
            if (!res.ok) {
                var err = await res.json().catch(function () { return {}; });
                throw new Error(err.error || '复制失败');
            }
            window.showToast('复制成功', 'success');
            allMachines = await API.machines.getAll();
            var machine = null;
            for (var i = 0; i < allMachines.length; i++) {
                if (allMachines[i].id === targetMachineId) { machine = allMachines[i]; break; }
            }
            renderInstrContent(machine);
            renderTable(allMachines);
        } catch (err) {
            window.showToast('复制失败: ' + err.message, 'error');
        }
    }

    // ================================================================
    // 批量导出
    // ================================================================

    async function exportSelectedQrcodes() {
        var ids = getSelectedIds();
        if (!ids.length) {
            window.showToast('请先勾选要导出的机床', 'warning');
            return;
        }

        batchExportBtn.disabled = true;
        batchExportBtn.textContent = '导出中...';

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
            a.download = 'machine_qrcodes.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(a.href);
            window.showToast('已导出 ' + ids.length + ' 台机床二维码', 'success');
        } catch (err) {
            window.showToast('导出失败: ' + err.message, 'error');
        } finally {
            batchExportBtn.textContent = '导出';
            exitBatchMode();
        }
    }

    // ================================================================
    // 点检模板
    // ================================================================

    function openTplModal(machineId, machineCode) {
        window.TplModal.open(machineId, machineCode);
    }

    // ================================================================
    // 新增机床
    // ================================================================

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

        window.Modal.openEdit('新增机床', html, function (close, fail) {
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
                fail();
            });
        });
    }

    // ================================================================
    // 编辑机床
    // ================================================================

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

            window.Modal.openEdit('编辑机床', html, function (close, fail) {
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
                    fail();
                });
            });
        }).catch(function (err) {
            window.showToast('加载失败: ' + err.message, 'error');
        });
    }

    // ================================================================
    // 删除机床
    // ================================================================

    function confirmDelete(id, code) {
        window.Modal.openDelete('确定要删除机床 "' + code + '" 吗？如有关联记录将无法删除。', function (close) {
            API.machines.remove(id).then(function () {
                window.showToast('删除成功', 'success');
                close();
                refresh();
            }).catch(function (err) {
                window.showToast(err.message, 'error');
                close();
            });
        });
    }

    // ================================================================
    // 工具函数
    // ================================================================

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
        openInstrModal: openInstrModal,
        handleInstrUpload: handleInstrUpload,
        deleteInstr: deleteInstr,
        copyInstr: copyInstr,
        confirmDelete: confirmDelete,
        enterBatchMode: enterBatchMode,
        exitBatchMode: exitBatchMode,
        onCbChange: onCbChange,
        exportSelectedQrcodes: exportSelectedQrcodes,
    };
})();
