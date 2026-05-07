(function () {
    'use strict';

    var modules = {
        overview: DashOverview,
        production: DashProduction,
        inspection: DashInspection,
        faults: DashFaults,
        machines: DashMachines
    };

    Object.keys(modules).forEach(function (name) {
        if (modules[name] && typeof modules[name].init === 'function') {
            modules[name].init();
        }
    });

    var navItems = document.querySelectorAll('.nav-item[data-panel]');
    var panels = document.querySelectorAll('.panel');

    navItems.forEach(function (btn) {
        btn.addEventListener('click', function () {
            switchPanel(btn.getAttribute('data-panel'));
        });
    });

    function switchPanel(name) {
        navItems.forEach(function (b) { b.classList.remove('active'); });
        var target = document.querySelector('.nav-item[data-panel="' + name + '"]');
        if (target) target.classList.add('active');
        panels.forEach(function (p) { p.classList.remove('active'); });
        var panel = document.getElementById('panel-' + name);
        if (panel) panel.classList.add('active');
        if (modules[name] && typeof modules[name].refresh === 'function') {
            modules[name].refresh();
        }
    }

    setInterval(function () {
        var p = document.getElementById('panel-overview');
        if (p && p.classList.contains('active')) {
            modules.overview.refresh();
        }
    }, 30000);

    window.showToast = function (message, type) {
        type = type || 'success';
        var container = document.getElementById('toastContainer');
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(function () {
            toast.classList.add('toast-out');
            toast.addEventListener('animationend', function () { toast.remove(); });
        }, 2500);
    };

    document.getElementById('logoutBtn').addEventListener('click', function () {
        if (confirm('确定要登出吗？')) {
            window.location.href = '/logout';
        }
    });
    // 编辑弹窗
    (function () {
        var overlay = document.getElementById('editModal');
        var titleEl = document.getElementById('editModalTitle');
        var bodyEl = document.getElementById('editModalBody');
        var confirmBtn = document.getElementById('editConfirmBtn');
        var cancelBtn = document.getElementById('editCancelBtn');
        var closeBtn = document.getElementById('editModalClose');
        var callback = null;

        function openEdit(title, html, onConfirm) {
            titleEl.textContent = title;
            bodyEl.innerHTML = html;
            callback = onConfirm;
            confirmBtn.disabled = false;
            confirmBtn.textContent = '保存';
            overlay.classList.add('open');
        }

        function closeEdit() {
            overlay.classList.remove('open');
            callback = null;
        }

        closeBtn.addEventListener('click', closeEdit);
        cancelBtn.addEventListener('click', closeEdit);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeEdit();
        });

        confirmBtn.addEventListener('click', function () {
            if (!callback) return;
            var cb = callback;
            callback = null;
            confirmBtn.disabled = true;
            confirmBtn.textContent = '保存中...';
            cb(
                function () {
                    confirmBtn.disabled = false;
                    confirmBtn.textContent = '保存';
                    closeEdit();
                },
                function () {
                    confirmBtn.disabled = false;
                    confirmBtn.textContent = '保存';
                    callback = cb;
                }
            );
        });



        window.Modal = window.Modal || {};
        window.Modal.openEdit = openEdit;
        window.Modal.closeEdit = closeEdit;
    })();

    // 删除确认弹窗
    (function () {
        var overlay = document.getElementById('deleteModal');
        var textEl = document.getElementById('deleteModalText');
        var confirmBtn = document.getElementById('deleteConfirmBtn');
        var cancelBtn = document.getElementById('deleteCancelBtn');
        var closeBtn = document.getElementById('deleteModalClose');
        var callback = null;

        function openDelete(text, onConfirm) {
            textEl.textContent = text || '确定要删除这条记录吗？此操作不可撤销。';
            callback = onConfirm;
            confirmBtn.disabled = false;
            confirmBtn.textContent = '确认删除';
            overlay.classList.add('open');
        }

        function closeDelete() {
            overlay.classList.remove('open');
            callback = null;
        }

        closeBtn.addEventListener('click', closeDelete);
        cancelBtn.addEventListener('click', closeDelete);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeDelete();
        });

        confirmBtn.addEventListener('click', function () {
            if (!callback) return;
            var cb = callback;
            callback = null;
            confirmBtn.disabled = true;
            confirmBtn.textContent = '删除中...';
            cb(function () {
                confirmBtn.disabled = false;
                confirmBtn.textContent = '确认删除';
                closeDelete();
            });
        });

        window.Modal.openDelete = openDelete;
        window.Modal.closeDelete = closeDelete;
    })();

    // 点检详情弹窗
    (function () {
        var overlay = document.getElementById('inspDetailModal');
        var titleEl = document.getElementById('inspDetailTitle');
        var bodyEl = document.getElementById('inspDetailBody');
        var closeBtn = document.getElementById('inspDetailCloseBtn');
        var closeX = document.getElementById('inspDetailClose');

        function open(record) {
            titleEl.textContent = '点检详情 - ' + (record.machine_code || '') + ' ' + (record.created_at || '');
            var html = '<div style="margin-bottom:12px;font-size:13px;color:var(--text-muted);">点检人：' + (record.operator_name || '-') + '</div>';
            if (record.details && record.details.length) {
                for (var i = 0; i < record.details.length; i++) {
                    var d = record.details[i];
                    var tagCls = d.result === '正常' ? 'tag-green' : 'tag-red';
                    var noteHtml = d.note ? '<span class="detail-note">(' + d.note + ')</span>' : '';
                    html += '<div class="insp-detail-item"><span class="detail-name">' + d.item_name + '</span><span class="tag ' + tagCls + '">' + d.result + '</span>' + noteHtml + '</div>';
                }
            } else {
                html += '<div style="color:var(--text-muted);font-size:13px;">无明细数据</div>';
            }
            if (record.remark) {
                html += '<div style="margin-top:12px;padding:10px;background:var(--surface-2);border-radius:var(--radius-sm);font-size:13px;color:var(--text-muted);">备注：' + record.remark + '</div>';
            }
            bodyEl.innerHTML = html;
            overlay.classList.add('open');
        }

        function close() {
            overlay.classList.remove('open');
        }

        closeBtn.addEventListener('click', close);
        closeX.addEventListener('click', close);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) close();
        });

        window.InspDetailModal = { open: open, close: close };
    })();
    // 点检模板弹窗
    (function () {
        var overlay = document.getElementById('tplModal');
        var titleEl = document.getElementById('tplModalTitle');
        var listEl = document.getElementById('tplList');
        var newNameInput = document.getElementById('tplNewName');
        var addBtn = document.getElementById('tplAddBtn');
        var copySource = document.getElementById('tplCopySource');
        var copyBtn = document.getElementById('tplCopyBtn');
        var closeBtn = document.getElementById('tplCloseBtn');
        var closeX = document.getElementById('tplModalClose');
        var importFile = document.getElementById('tplImportFile');
        var importBtn = document.getElementById('tplImportBtn');
        var importName = document.getElementById('tplImportName');
        var importConfirm = document.getElementById('tplImportConfirm');
        var currentMachineId = null;
        var csvItems = null;

        function open(machineId, machineCode) {
            currentMachineId = machineId;
            titleEl.textContent = '点检模板 - ' + machineCode;
            overlay.classList.add('open');
            resetImport();
            loadMachines();
            loadTemplates();
        }

        function close() {
            overlay.classList.remove('open');
            currentMachineId = null;
            resetImport();
        }

        function resetImport() {
            importFile.value = '';
            importName.textContent = '';
            importConfirm.style.display = 'none';
            csvItems = null;
        }

        function loadMachines() {
            API.machines.getAll().then(function (machines) {
                copySource.innerHTML = '<option value="">请选择源设备</option>';
                for (var i = 0; i < machines.length; i++) {
                    if (machines[i].id !== currentMachineId) {
                        var opt = document.createElement('option');
                        opt.value = machines[i].id;
                        opt.textContent = machines[i].machine_code + ' ' + machines[i].machine_name;
                        copySource.appendChild(opt);
                    }
                }
            }).catch(function (e) { console.error(e); });
        }

        function loadTemplates() {
            API.inspectionTemplates.getAll(currentMachineId).then(function (items) {
                renderList(items);
            }).catch(function (err) {
                window.showToast('加载模板失败: ' + err.message, 'error');
            });
        }

        function renderList(items) {
            if (!items.length) {
                listEl.innerHTML = '<div class="empty-state" style="padding:24px 0;"><div class="empty-text">暂无点检项目，请添加或从其他设备复制</div></div>';
                return;
            }
            var html = '';
            for (var i = 0; i < items.length; i++) {
                var item = items[i];
                var safeName = String(item.item_name).replace(/'/g, "\\'").replace(/"/g, '&quot;');
                html += '<div class="tpl-item">';
                html += '<span class="tpl-order">' + (i + 1) + '</span>';
                html += '<span class="tpl-name">' + item.item_name + '</span>';
                html += '<span class="tpl-actions">';
                html += '<button class="btn btn-ghost" data-action="edit" data-id="' + item.id + '" data-name="' + safeName + '">编辑</button>';
                html += '<button class="btn btn-danger" data-action="delete" data-id="' + item.id + '">删除</button>';
                html += '</span></div>';
            }
            listEl.innerHTML = html;
            var buttons = listEl.querySelectorAll('button[data-action]');
            for (var j = 0; j < buttons.length; j++) {
                buttons[j].addEventListener('click', handleItemClick);
            }
        }

        function handleItemClick(e) {
            var btn = e.currentTarget;
            var action = btn.getAttribute('data-action');
            var id = parseInt(btn.getAttribute('data-id'), 10);
            if (action === 'edit') {
                var oldName = btn.getAttribute('data-name');
                var newName = prompt('修改点检项目名称：', oldName);
                if (newName === null || newName.trim() === '' || newName.trim() === oldName) return;
                API.inspectionTemplates.update(id, { item_name: newName.trim() })
                    .then(function () { loadTemplates(); window.showToast('更新成功', 'success'); })
                    .catch(function (err) { window.showToast('更新失败: ' + err.message, 'error'); });
            } else if (action === 'delete') {
                if (!confirm('确定删除这个点检项目吗？')) return;
                API.inspectionTemplates.remove(id)
                    .then(function () { loadTemplates(); window.showToast('删除成功', 'success'); })
                    .catch(function (err) { window.showToast('删除失败: ' + err.message, 'error'); });
            }
        }

        addBtn.addEventListener('click', function () {
            var name = newNameInput.value.trim();
            if (!name) { window.showToast('请输入项目名称', 'warning'); newNameInput.focus(); return; }
            API.inspectionTemplates.create({ machine_id: currentMachineId, item_name: name })
                .then(function () { newNameInput.value = ''; loadTemplates(); window.showToast('添加成功', 'success'); })
                .catch(function (err) { window.showToast('添加失败: ' + err.message, 'error'); });
        });

        newNameInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { e.preventDefault(); addBtn.click(); }
        });

        copyBtn.addEventListener('click', function () {
            var sourceId = parseInt(copySource.value, 10);
            if (!sourceId) { window.showToast('请选择源设备', 'warning'); return; }
            if (!confirm('复制将覆盖当前设备已有的点检模板，确定继续？')) return;
            API.inspectionTemplates.copy(sourceId, currentMachineId)
                .then(function (result) { loadTemplates(); window.showToast('已复制 ' + result.copied + ' 个项目', 'success'); })
                .catch(function (err) { window.showToast('复制失败: ' + err.message, 'error'); });
        });

        importBtn.addEventListener('click', function () { importFile.click(); });

        importFile.addEventListener('change', function () {
            var file = importFile.files[0];
            if (!file) return;
            importName.textContent = file.name;
            importConfirm.style.display = 'inline-flex';
            var reader = new FileReader();
            reader.onload = function (e) {
                var text = e.target.result;
                var lines = text.split(/\r?\n/);
                csvItems = [];
                for (var i = 0; i < lines.length; i++) {
                    var line = lines[i].trim();
                    if (line) { csvItems.push(line.split(',')[0].trim()); }
                }
            };
            reader.readAsText(file, 'UTF-8');
        });

        importConfirm.addEventListener('click', function () {
            if (!csvItems || !csvItems.length) { window.showToast('文件内容为空', 'warning'); return; }
            if (!confirm('导入将覆盖当前设备已有的点检模板，共 ' + csvItems.length + ' 个项目，确定继续？')) return;
            API.inspectionTemplates.importCSV(currentMachineId, csvItems)
                .then(function (result) { loadTemplates(); window.showToast('成功导入 ' + result.imported + ' 个项目', 'success'); resetImport(); })
                .catch(function (err) { window.showToast });
        });

        closeBtn.addEventListener('click', close);
        closeX.addEventListener('click', close);
        overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });

        window.TplModal = { open: open, close: close };
    })();

    // 导出按钮
    (function () {
        var exportBtn = document.getElementById('inspExportBtn');
        if (!exportBtn) return;
        exportBtn.addEventListener('click', function () {
            var filterMachine = document.getElementById('inspFilterMachine');
            var machineId = filterMachine ? filterMachine.value : '';
            API.inspection.export(machineId);
        });
    })();

})();
