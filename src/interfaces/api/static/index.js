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

        // Toggle required on file path field (not needed for sqlserver/oracle/bigquery)
        const pathField = document.getElementById(prefix);
        if (pathField) {
            if (type === 'sqlserver' || type === 'oracle' || type === 'bigquery') {
                pathField.removeAttribute('required');
            } else {
                pathField.setAttribute('required', '');
            }
        }

        // Keep Oracle client dir conditional on thick mode selection
        if (type === 'oracle') {
            updateOracleClientDir(prefix);
        }
    }

    sourceType.addEventListener('change', () => {
        updateFields('source');
        updateQueryHint();
    });
    targetType.addEventListener('change', () => updateFields('target'));

    // ── Dica dinâmica no campo de consulta personalizada ─────────
    function updateQueryHint() {
        const type = sourceType.value;
        const textarea = document.getElementById('source_custom_query');
        const hint = document.getElementById('custom-query-hint');
        if (!textarea || !hint) return;

        const hints = {
            csv:       { ph: 'idade > 30 and cidade == "SP"', txt: 'Use sintaxe <a href="https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.query.html" target="_blank">pandas.DataFrame.query()</a>. Ex.: <code>idade > 30 and cidade == "SP"</code>' },
            parquet:   { ph: 'idade > 30 and cidade == "SP"', txt: 'Use sintaxe <a href="https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.query.html" target="_blank">pandas.DataFrame.query()</a>. Ex.: <code>idade > 30 and cidade == "SP"</code>' },
            sqlite:    { ph: 'SELECT * FROM people WHERE age > 30', txt: 'Escreva uma consulta SQL válida para SQLite. A tabela informada acima é ignorada quando uma consulta personalizada é fornecida.' },
            sqlserver: { ph: 'SELECT * FROM [dbo].[people] WHERE age > 30', txt: 'Escreva uma consulta T-SQL válida. A tabela informada acima é ignorada quando uma consulta personalizada é fornecida.' },
            oracle:    { ph: 'SELECT * FROM "SCHEMA"."TABELA" WHERE ROWNUM <= 1000', txt: 'Escreva uma consulta Oracle SQL válida. A tabela informada acima é ignorada quando uma consulta personalizada é fornecida.' },
            bigquery:  { ph: 'SELECT * FROM `projeto.dataset.tabela` WHERE data > "2024-01-01"', txt: 'Escreva uma consulta BigQuery Standard SQL válida. A tabela informada acima é ignorada quando uma consulta personalizada é fornecida.' },
        };
        const h = hints[type] || hints.csv;
        textarea.placeholder = h.ph;
        hint.innerHTML = h.txt;
    }

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
            } else if (sourceType.value === 'oracle') {
                if (!document.getElementById('source_oracle_dsn').value.trim()) {
                    alert('Informe o DSN de conexão da origem Oracle.');
                    return false;
                }
                if (!document.getElementById('source_table_name_oracle').value.trim()) {
                    alert('Informe o nome da tabela de origem Oracle.');
                    return false;
                }
            } else if (sourceType.value === 'bigquery') {
                if (!document.getElementById('source_bq_credentials_file').value.trim()) {
                    alert('Informe o arquivo de credenciais JSON da origem BigQuery.');
                    return false;
                }
                if (!document.getElementById('source_table_name_bq').value.trim()) {
                    alert('Informe a tabela de origem BigQuery (dataset.tabela).');
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
            } else if (targetType.value === 'oracle') {
                if (!document.getElementById('target_oracle_dsn').value.trim()) {
                    alert('Informe o DSN de conexão do destino Oracle.');
                    return false;
                }
                if (!document.getElementById('target_table_name_oracle').value.trim()) {
                    alert('Informe o nome da tabela de destino Oracle.');
                    return false;
                }
            } else if (targetType.value === 'bigquery') {
                if (!document.getElementById('target_bq_credentials_file').value.trim()) {
                    alert('Informe o arquivo de credenciais JSON do destino BigQuery.');
                    return false;
                }
                if (!document.getElementById('target_table_name_bq').value.trim()) {
                    alert('Informe a tabela de destino BigQuery (dataset.tabela).');
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
            : sourceType.value === 'oracle'
                ? document.getElementById('source_oracle_dsn').value
                : sourceType.value === 'bigquery'
                    ? document.getElementById('source_bq_credentials_file').value
                    : document.getElementById('source').value;
        const tgtPath = targetType.value === 'sqlserver'
            ? document.getElementById('target_connection_string').value
            : targetType.value === 'oracle'
                ? document.getElementById('target_oracle_dsn').value
                : targetType.value === 'bigquery'
                    ? document.getElementById('target_bq_credentials_file').value
                    : document.getElementById('target').value;

        function extras(type, tblId, sepId, colId, encId, tblSqlId, tblOracleId, oracleModePrefix) {
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
            if (type === 'ORACLE') {
                const t = document.getElementById(tblOracleId).value;
                if (t) items.push('Tabela: <strong>' + esc(t) + '</strong>');
                const modeEl = document.querySelector('input[name="' + oracleModePrefix + '_oracle_mode"]:checked');
                if (modeEl) items.push('Modo: <strong>' + esc(modeEl.value) + '</strong>');
            }
            if (type === 'BIGQUERY') {
                const t = document.getElementById(oracleModePrefix + '_table_name_bq').value;
                if (t) items.push('Tabela: <strong>' + esc(t) + '</strong>');
                const proj = document.getElementById(oracleModePrefix + '_bq_project_id').value;
                if (proj) items.push('Project: <strong>' + esc(proj) + '</strong>');
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
          +      extras(srcType, 'source_table_name', 'source_sep_file', 'source_columns', 'source_encoding', 'source_table_name_sql', 'source_table_name_oracle', 'source')
          + '  </div>'
          + '  <div class="summary-arrow">'
          + '    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>'
          + '  </div>'
          + '  <div class="summary-block summary-target">'
          + '    <span class="section-badge target-badge">SAÍDA</span>'
          + '    <div class="summary-type">' + esc(tgtType === 'SQLSERVER' ? 'SQL SERVER' : tgtType) + '</div>'
          + '    <div class="summary-path">' + esc(tgtPath) + '</div>'
          +      extras(tgtType, 'target_table_name', 'target_sep_file', 'target_columns', 'target_encoding', 'target_table_name_sql', 'target_table_name_oracle', 'target')
          + '  </div>'
          + '</div>';

        // Adiciona consulta personalizada ao resumo, se preenchida
        const customQ = (document.getElementById('source_custom_query') || {}).value || '';
        if (customQ.trim()) {
            document.getElementById('summary-content').innerHTML +=
                '<div class="mt-3 p-3 bg-body-secondary rounded-3">'
              + '  <div class="d-flex align-items-center gap-2 mb-2">'
              + '    <i class="bi bi-funnel text-primary"></i>'
              + '    <strong>Consulta personalizada</strong>'
              + '  </div>'
              + '  <pre class="mb-0 small bg-white p-2 rounded border" style="white-space:pre-wrap">' + esc(customQ.trim()) + '</pre>'
              + '</div>';
        }
    }

    window.nextStep = function (current) {
        if (!validateStep(current)) return;
        if (current === 2) buildSummary();
        goToStep(current + 1);
    };

    // Inicializa
    updateFields('source');
    updateFields('target');
    updateQueryHint();
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

// ── BigQuery: testar conexão ────────────────────────────────────
window.testBigQueryConnection = function (prefix) {
    const fileEl = document.getElementById(prefix + '_bq_credentials_file');
    const projEl = document.getElementById(prefix + '_bq_project_id');
    const statusEl = document.getElementById(prefix + '-bq-conn-status');
    const credFile = fileEl ? fileEl.value.trim() : '';
    const projectId = projEl ? projEl.value.trim() : '';

    if (!credFile) {
        statusEl.innerHTML = '<span class="badge bg-warning-subtle text-warning-emphasis">'
            + '<i class="bi bi-exclamation-triangle me-1"></i>Informe o arquivo JSON</span>';
        return;
    }

    statusEl.innerHTML = '<span class="badge bg-secondary-subtle text-secondary-emphasis">'
        + '<span class="spinner-border spinner-border-sm me-1" style="width:.7rem;height:.7rem"></span>Testando...</span>';

    const body = new URLSearchParams({ credentials_file: credFile, project_id: projectId });
    fetch('/test-connection-bigquery', { method: 'POST', body })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                statusEl.innerHTML = '<span class="badge bg-success-subtle text-success-emphasis">'
                    + '<i class="bi bi-check-circle me-1"></i>' + data.message + '</span>';
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

// ── Oracle: alternar visibilidade do diretório do client ────────
window.updateOracleClientDir = function (prefix) {
    const thickRadio = document.getElementById(prefix + '_oracle_mode_thick');
    const row = document.getElementById(prefix + '-oracle-client-dir-row');
    if (!row) return;
    if (thickRadio && thickRadio.checked) {
        row.classList.remove('d-none');
    } else {
        row.classList.add('d-none');
    }
};

// ── Oracle: testar conexão ──────────────────────────────────────
window.testOracleConnection = function (prefix) {
    const dsn = document.getElementById(prefix + '_oracle_dsn').value.trim();
    const statusEl = document.getElementById(prefix + '-oracle-conn-status');
    const modeEl = document.querySelector('input[name="' + prefix + '_oracle_mode"]:checked');
    const mode = modeEl ? modeEl.value : 'thin';
    const clientDirEl = document.getElementById(prefix + '_oracle_client_dir');
    const clientDir = clientDirEl ? clientDirEl.value.trim() : '';

    if (!dsn) {
        statusEl.innerHTML = '<span class="badge bg-warning-subtle text-warning-emphasis">'
            + '<i class="bi bi-exclamation-triangle me-1"></i>Informe o DSN</span>';
        return;
    }

    statusEl.innerHTML = '<span class="badge bg-secondary-subtle text-secondary-emphasis">'
        + '<span class="spinner-border spinner-border-sm me-1" style="width:.7rem;height:.7rem"></span>Testando...</span>';

    const body = new URLSearchParams({ dsn, mode, client_lib_dir: clientDir });
    fetch('/test-connection-oracle', { method: 'POST', body })
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
