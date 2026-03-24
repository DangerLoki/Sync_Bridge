document.addEventListener('DOMContentLoaded', () => {
    const sourceType = document.getElementById('source_type');
    const targetType = document.getElementById('target_type');

    // ── Visibilidade de campos por tipo ──────────────────────────
    function updateFields(prefix) {
        const type = document.getElementById(prefix + '_type').value;
        document.querySelectorAll('.' + prefix + '-field').forEach(el => {
            el.classList.add('d-none');
        });
        document.querySelectorAll('.' + prefix + '-' + type + '-field').forEach(el => {
            el.classList.remove('d-none');
        });

        // Toggle required on file path field (not needed for sqlserver)
        const pathField = document.getElementById(prefix);
        if (pathField) {
            if (type === 'sqlserver') {
                pathField.removeAttribute('required');
            } else {
                pathField.setAttribute('required', '');
            }
        }
    }

    sourceType.addEventListener('change', () => updateFields('source'));
    targetType.addEventListener('change', () => updateFields('target'));

    // ── Wizard navigation ───────────────────────────────────────
    const panels = document.querySelectorAll('.step-panel');
    const dots   = document.querySelectorAll('.stepper-step');
    const lines  = document.querySelectorAll('.stepper-line');

    function goToStep(n) {
        panels.forEach(p => {
            p.classList.remove('active');
            p.classList.add('d-none');
        });
        const activePanel = document.getElementById('step-' + n);
        activePanel.classList.remove('d-none');
        activePanel.classList.add('active');

        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i + 1 === n);
            dot.classList.toggle('done',   i + 1 < n);
        });
        lines.forEach((line, i) => {
            line.classList.toggle('done', i + 1 < n);
        });
    }
    window.goToStep = goToStep;

    function validateStep(n) {
        if (n === 1) {
            if (sourceType.value === 'sqlserver') {
                if (!document.getElementById('source_connection_string').value.trim()) {
                    alert('Informe a string de conexão da origem.');
                    return false;
                }
                if (!document.getElementById('source_table_name_sql').value.trim()) {
                    alert('Informe o nome da tabela de origem.');
                    return false;
                }
            } else {
                if (!document.getElementById('source').value.trim()) {
                    alert('Informe o caminho da origem.');
                    return false;
                }
                if (sourceType.value === 'sqlite' &&
                    !document.getElementById('source_table_name').value.trim()) {
                    alert('Informe o nome da tabela de origem.');
                    return false;
                }
            }
        }
        if (n === 2) {
            if (targetType.value === 'sqlserver') {
                if (!document.getElementById('target_connection_string').value.trim()) {
                    alert('Informe a string de conexão do destino.');
                    return false;
                }
                if (!document.getElementById('target_table_name_sql').value.trim()) {
                    alert('Informe o nome da tabela de destino.');
                    return false;
                }
            } else {
                if (!document.getElementById('target').value.trim()) {
                    alert('Informe o caminho do destino.');
                    return false;
                }
                if (targetType.value === 'sqlite' &&
                    !document.getElementById('target_table_name').value.trim()) {
                    alert('Informe o nome da tabela de destino.');
                    return false;
                }
            }
        }
        return true;
    }

    function selText(id) {
        const el = document.getElementById(id);
        return el ? el.options[el.selectedIndex].text : '';
    }

    function esc(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function buildSummary() {
        const srcType = sourceType.value.toUpperCase();
        const tgtType = targetType.value.toUpperCase();

        const srcPath = sourceType.value === 'sqlserver'
            ? document.getElementById('source_connection_string').value
            : document.getElementById('source').value;
        const tgtPath = targetType.value === 'sqlserver'
            ? document.getElementById('target_connection_string').value
            : document.getElementById('target').value;

        function extras(type, tblId, sepId, colId, encId, tblSqlId) {
            const items = [];
            if (type === 'SQLITE') {
                const t = document.getElementById(tblId).value;
                if (t) items.push('Tabela: <strong>' + esc(t) + '</strong>');
            }
            if (type === 'CSV') {
                items.push('Separador: <strong>' + esc(selText(sepId)) + '</strong>');
                const enc = document.getElementById(encId).value || 'utf-8-sig';
                items.push('Encoding: <strong>' + esc(enc) + '</strong>');
            }
            if (type === 'PARQUET') {
                const comp = document.getElementById(colId);
                if (comp) items.push('Compressão: <strong>' + esc(comp.options[comp.selectedIndex].text) + '</strong>');
            }
            if (type === 'SQLSERVER') {
                const t = document.getElementById(tblSqlId).value;
                if (t) items.push('Tabela: <strong>' + esc(t) + '</strong>');
            }
            return items.length
                ? '<div class="summary-extra mt-2">' + items.join(' &middot; ') + '</div>'
                : '';
        }

        document.getElementById('summary-content').innerHTML =
            '<div class="summary-row">'
          + '  <div class="summary-block summary-source">'
          + '    <span class="section-badge source-badge">ENTRADA</span>'
          + '    <div class="summary-type">' + esc(srcType === 'SQLSERVER' ? 'SQL SERVER' : srcType) + '</div>'
          + '    <div class="summary-path">' + esc(srcPath) + '</div>'
          +      extras(srcType, 'source_table_name', 'source_sep_file', 'source_columns', 'source_encoding', 'source_table_name_sql')
          + '  </div>'
          + '  <div class="summary-arrow">'
          + '    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>'
          + '  </div>'
          + '  <div class="summary-block summary-target">'
          + '    <span class="section-badge target-badge">SAÍDA</span>'
          + '    <div class="summary-type">' + esc(tgtType === 'SQLSERVER' ? 'SQL SERVER' : tgtType) + '</div>'
          + '    <div class="summary-path">' + esc(tgtPath) + '</div>'
          +      extras(tgtType, 'target_table_name', 'target_sep_file', 'target_columns', 'target_encoding', 'target_table_name_sql')
          + '  </div>'
          + '</div>';
    }

    window.nextStep = function (current) {
        if (!validateStep(current)) return;
        if (current === 2) buildSummary();
        goToStep(current + 1);
    };

    // Inicializa
    updateFields('source');
    updateFields('target');
    goToStep(1);
});

// ── File browser modal ──────────────────────────────────────────
(function () {
    let _targetFieldId = null;
    let _selectedPath  = null;
    let _modal         = null;

    window.openBrowser = function (fieldId) {
        _targetFieldId = fieldId;
        _selectedPath  = null;

        if (!_modal) {
            _modal = new bootstrap.Modal(document.getElementById('fileBrowserModal'));
        }

        // Start from current field value or working dir
        const current = document.getElementById(fieldId).value.trim() || '.';
        _modal.show();
        loadDir(current);
    };

    function loadDir(path) {
        document.getElementById('browser-select-btn').disabled = true;
        _selectedPath = null;

        const list = document.getElementById('browser-list');
        list.innerHTML = '<div class="text-center py-4 text-body-secondary">'
            + '<div class="spinner-border spinner-border-sm me-2"></div>Carregando...</div>';

        fetch('/browse?path=' + encodeURIComponent(path))
            .then(r => r.json())
            .then(data => renderDir(data))
            .catch(() => {
                list.innerHTML = '<div class="text-center py-4 text-danger">'
                    + '<i class="bi bi-exclamation-triangle me-2"></i>Erro ao carregar diretório.</div>';
            });
    }

    function renderDir(data) {
        document.getElementById('browser-current-path').textContent = data.current;

        const list = document.getElementById('browser-list');
        let html = '';

        if (data.parent) {
            html += '<button type="button" class="list-group-item list-group-item-action browser-item py-2 px-3"'
                + ' data-path="' + esc(data.parent) + '" data-is-dir="true">'
                + '<i class="bi bi-arrow-up-circle text-secondary me-2"></i>'
                + '<span class="text-secondary fst-italic">..</span>'
                + '</button>';
        }

        data.entries.forEach(entry => {
            const icon = entry.is_dir
                ? '<i class="bi bi-folder-fill text-warning me-2"></i>'
                : '<i class="bi bi-file-earmark text-secondary me-2"></i>';
            html += '<button type="button" class="list-group-item list-group-item-action browser-item py-2 px-3'
                + (entry.is_dir ? '' : ' browser-file') + '"'
                + ' data-path="' + esc(entry.path) + '" data-is-dir="' + entry.is_dir + '">'
                + icon + esc(entry.name)
                + '</button>';
        });

        if (!html) {
            html = '<div class="text-center py-4 text-body-secondary">Diretório vazio.</div>';
        }

        list.innerHTML = html;

        list.querySelectorAll('.browser-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const isDir = btn.dataset.isDir === 'true';
                const path  = btn.dataset.path;

                if (isDir) {
                    loadDir(path);
                } else {
                    // Deselect previous
                    list.querySelectorAll('.browser-item.active').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    _selectedPath = path;
                    document.getElementById('browser-select-btn').disabled = false;
                }
            });

            // Double-click on file also confirms
            if (btn.dataset.isDir === 'false') {
                btn.addEventListener('dblclick', () => {
                    _selectedPath = btn.dataset.path;
                    confirmBrowse();
                });
            }
        });
    }

    window.confirmBrowse = function () {
        if (_selectedPath && _targetFieldId) {
            document.getElementById(_targetFieldId).value = _selectedPath;
        }
        if (_modal) _modal.hide();
    };

    function esc(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }
}());

// ── SQL Server: testar conexão ──────────────────────────────────
window.testConnection = function (inputId, statusId) {
    const connStr = document.getElementById(inputId).value.trim();
    const statusEl = document.getElementById(statusId);

    if (!connStr) {
        statusEl.innerHTML = '<span class="badge bg-warning-subtle text-warning-emphasis">'
            + '<i class="bi bi-exclamation-triangle me-1"></i>Informe a string de conexão</span>';
        return;
    }

    statusEl.innerHTML = '<span class="badge bg-secondary-subtle text-secondary-emphasis">'
        + '<span class="spinner-border spinner-border-sm me-1" style="width:.7rem;height:.7rem"></span>Testando...</span>';

    const body = new URLSearchParams({ connection_string: connStr });
    fetch('/test-connection', { method: 'POST', body })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                statusEl.innerHTML = '<span class="badge bg-success-subtle text-success-emphasis">'
                    + '<i class="bi bi-check-circle me-1"></i>Conexão OK</span>';
            } else {
                statusEl.innerHTML = '<span class="badge bg-danger-subtle text-danger-emphasis" title="'
                    + data.message.replace(/"/g, '&quot;') + '">'
                    + '<i class="bi bi-x-circle me-1"></i>Falha — passe o mouse para ver o erro</span>';
            }
        })
        .catch(() => {
            statusEl.innerHTML = '<span class="badge bg-danger-subtle text-danger-emphasis">'
                + '<i class="bi bi-x-circle me-1"></i>Erro ao chamar o servidor</span>';
        });
};
