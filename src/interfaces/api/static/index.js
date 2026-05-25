document.addEventListener('DOMContentLoaded', () => {
    const sourceType = document.getElementById('source_type');
    const targetType = document.getElementById('target_type');
    const enableStreaming = document.getElementById('enable_streaming');
    const chunkSize = document.getElementById('chunk_size');
    const chunkSizeRow = document.getElementById('chunk-size-row');

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

    function updateStreamingControls() {
        if (!enableStreaming || !chunkSize || !chunkSizeRow) return;

        if (enableStreaming.checked) {
            chunkSize.readOnly = false;
            chunkSizeRow.classList.remove('is-disabled');
            if (parseInt(chunkSize.value || '0', 10) <= 0) {
                chunkSize.value = '10000';
            }
        } else {
            chunkSize.value = '0';
            chunkSize.readOnly = true;
            chunkSizeRow.classList.add('is-disabled');
        }
    }

    if (enableStreaming) {
        enableStreaming.addEventListener('change', updateStreamingControls);
    }

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
            if (enableStreaming && enableStreaming.checked &&
                parseInt((chunkSize || {}).value || '0', 10) <= 0) {
                alert('Informe um número de linhas por lote maior que zero.');
                chunkSize.focus();
                return false;
            }
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

        // Adiciona chunk_size ao resumo
        const chunkSize = parseInt((document.getElementById('chunk_size') || {}).value || '0', 10);
        if (chunkSize > 0) {
            document.getElementById('summary-content').innerHTML +=
                '<div class="mt-3 p-3 bg-body-secondary rounded-3">'
              + '  <div class="d-flex align-items-center gap-2">'
              + '    <i class="bi bi-layers text-primary"></i>'
              + '    <strong>Modo streaming:</strong>&nbsp;' + esc(String(chunkSize)) + ' linhas por chunk'
              + '  </div>'
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
    updateStreamingControls();
    goToStep(1);
});

// ── File browser modal ──────────────────────────────────────────
(function () {
    let _targetFieldId = null;
    let _selectedPath  = null;
    let _modal         = null;
    let _writeMode     = false;
    let _currentDir    = '.';

    window.openBrowser = function (fieldId, writeMode) {
        _targetFieldId = fieldId;
        _selectedPath  = null;
        _writeMode     = !!writeMode;

        if (!_modal) {
            _modal = new bootstrap.Modal(document.getElementById('fileBrowserModal'));
        }

        // Show / hide write-mode filename row
        const writeRow = document.getElementById('browser-write-row');
        const filenameInput = document.getElementById('browser-filename-input');
        const modalTitle = document.querySelector('#fileBrowserModal .modal-title');
        if (_writeMode) {
            writeRow.classList.remove('d-none');
            filenameInput.value = '';
            if (modalTitle) modalTitle.textContent = 'Escolher pasta de destino';
            // Select button always enabled in write mode — user can confirm current dir
            document.getElementById('browser-select-btn').disabled = false;
            filenameInput.oninput = null;
        } else {
            writeRow.classList.add('d-none');
            if (modalTitle) modalTitle.textContent = 'Navegar arquivos';
            filenameInput.oninput = null;
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
            .then(data => {
                _currentDir = data.current;
                renderDir(data);
                // In write mode the select button is always enabled
                if (_writeMode) {
                    document.getElementById('browser-select-btn').disabled = false;
                }
            })
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

                    if (_writeMode) {
                        // Pre-fill filename input with the selected file's name
                        const fname = path.split('/').pop();
                        const filenameInput = document.getElementById('browser-filename-input');
                        filenameInput.value = fname;
                        document.getElementById('browser-select-btn').disabled = !fname;
                    } else {
                        document.getElementById('browser-select-btn').disabled = false;
                    }
                }
            });

            // Double-click on file also confirms
            if (btn.dataset.isDir === 'false') {
                btn.addEventListener('dblclick', () => {
                    _selectedPath = btn.dataset.path;
                    if (_writeMode) {
                        const fname = btn.dataset.path.split('/').pop();
                        document.getElementById('browser-filename-input').value = fname;
                    }
                    confirmBrowse();
                });
            }
        });
    }

    window.confirmBrowse = function () {
        if (_targetFieldId) {
            if (_writeMode) {
                const fname = (document.getElementById('browser-filename-input').value || '').trim();
                const dir = _currentDir.replace(/\/+$/, '');
                // If filename typed: dir/filename. Otherwise: just dir (user completes in the field).
                document.getElementById(_targetFieldId).value = fname ? dir + '/' + fname : dir;
            } else if (_selectedPath) {
                document.getElementById(_targetFieldId).value = _selectedPath;
            }
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
// ── Transfer streaming terminal ─────────────────────────────────
(function () {

    function esc(str) {
        const d = document.createElement('div');
        d.textContent = String(str || '');
        return d.innerHTML;
    }

    window.copyTerminalLogs = function () {
        const pre = document.getElementById('terminal-output');
        if (!pre) return;
        navigator.clipboard.writeText(pre.innerText || pre.textContent).then(() => {
            const icon = document.querySelector('#terminal-copy-btn i');
            if (icon) {
                icon.className = 'bi bi-clipboard-check';
                setTimeout(() => { icon.className = 'bi bi-clipboard'; }, 2000);
            }
        });
    };

    document.addEventListener('DOMContentLoaded', function () {
        const btn = document.getElementById('run-transfer-btn');
        if (!btn) return;
        btn.addEventListener('click', runTransferStream);
    });

    function runTransferStream() {
        const form        = document.getElementById('transfer-form');
        const terminal    = document.getElementById('transfer-terminal');
        const output      = document.getElementById('terminal-output');
        const progressBar = document.getElementById('terminal-progress-bar');
        const progressLbl = document.getElementById('terminal-progress-label');
        const rowsLbl     = document.getElementById('terminal-rows-label');
        const footer      = document.getElementById('terminal-result-footer');
        const titleText   = document.getElementById('terminal-title-text');
        const btn         = document.getElementById('run-transfer-btn');

        // ── reset ──────────────────────────────────────────────
        output.innerHTML         = '';
        progressBar.style.width  = '5%';
        progressBar.className    = 'progress-bar progress-bar-striped progress-bar-animated';
        progressLbl.textContent  = 'Conectando...';
        rowsLbl.textContent      = '';
        footer.className         = 'd-none';
        footer.innerHTML         = '';
        titleText.textContent    = 'SyncBridge \u2014 transfer\u00eancia em andamento';

        terminal.classList.remove('d-none');
        terminal.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        btn.disabled  = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" '
                      + 'style="width:.9rem;height:.9rem"></span>Transferindo...';

        let rowsRead = 0, rowsWritten = 0;

        function appendLine(html) {
            const span = document.createElement('span');
            span.innerHTML = html + '\n';
            output.appendChild(span);
            output.scrollTop = output.scrollHeight;
        }

        function resetBtn() {
            btn.disabled  = false;
            btn.innerHTML = '<i class="bi bi-play-fill"></i> Executar transfer\u00eancia';
        }

        function handleEvent(event) {
            const ts = new Date().toLocaleTimeString('pt-BR', { hour12: false });

            if (event.type === 'log') {
                const lvl    = event.level || 'info';
                const prefix = { debug: '\u00b7', info: '\u25b8', warning: '\u26a0', error: '\u2716' }[lvl] || '\u25b8';
                appendLine(`<span class="log-${esc(lvl)}">${ts}  ${prefix}  ${esc(event.msg)}</span>`);
            }

            if (event.type === 'start') {
                appendLine(`<span class="log-start">\u25ba  ${esc(event.msg)}</span>`);
                progressLbl.textContent = 'Transferindo...';
                progressBar.style.width = '15%';
            }

            if (event.type === 'progress') {
                rowsRead    = event.rows_read    || rowsRead;
                rowsWritten = event.rows_written || rowsWritten;
                rowsLbl.textContent     = `${rowsRead.toLocaleString('pt-BR')} lidas \u00b7 ${rowsWritten.toLocaleString('pt-BR')} escritas`;
                progressLbl.textContent = event.done
                    ? 'Finalizando...'
                    : `Chunk ${event.chunk_index + 1} processado`;
            }

            if (event.type === 'done') {
                rowsRead    = event.rows_read;
                rowsWritten = event.rows_written;
                progressBar.style.width  = '100%';
                progressBar.className    = 'progress-bar bg-success';
                progressLbl.textContent  = 'Conclu\u00eddo!';
                rowsLbl.textContent      = `${rowsRead.toLocaleString('pt-BR')} lidas \u00b7 ${rowsWritten.toLocaleString('pt-BR')} escritas`;
                titleText.textContent    = 'SyncBridge \u2014 conclu\u00eddo \u2713';

                appendLine(`<span class="log-success">\u2714  Transfer\u00eancia conclu\u00edda \u2014 `
                         + `${rowsRead.toLocaleString('pt-BR')} linhas lidas, `
                         + `${rowsWritten.toLocaleString('pt-BR')} escritas.</span>`);

                footer.className = '';
                footer.innerHTML =
                    '<div class="d-flex align-items-center gap-3 mb-3">'
                  + '  <span class="d-inline-flex align-items-center justify-content-center bg-success text-white rounded-circle flex-shrink-0" style="width:36px;height:36px"><i class="bi bi-check-lg"></i></span>'
                  + '  <strong class="result-success fs-6">Transfer\u00eancia conclu\u00edda com sucesso</strong>'
                  + '</div>'
                  + '<div class="row g-2 small">'
                  + '  <div class="col-sm-6"><span class="text-secondary">Status:</span> <strong>' + esc(event.status || 'SUCCESS') + '</strong></div>'
                  + '  <div class="col-sm-6"><span class="text-secondary">Origem:</span> <strong>' + esc(event.source) + '</strong></div>'
                  + '  <div class="col-sm-6"><span class="text-secondary">Destino:</span> <strong>' + esc(event.target) + '</strong></div>'
                  + '  <div class="col-sm-6"><span class="text-secondary">Linhas lidas:</span> <strong>' + rowsRead.toLocaleString('pt-BR') + '</strong></div>'
                  + '  <div class="col-sm-6"><span class="text-secondary">Linhas escritas:</span> <strong>' + rowsWritten.toLocaleString('pt-BR') + '</strong></div>'
                  + '</div>'
                  + '<div class="mt-3">'
                  + '  <button type="button" class="btn btn-outline-light btn-sm" onclick="location.reload()">'
                  + '    <i class="bi bi-arrow-repeat me-1"></i>Nova transfer\u00eancia'
                  + '  </button>'
                  + '</div>';

                resetBtn();
            }

            if (event.type === 'error') {
                progressBar.style.width  = '100%';
                progressBar.className    = 'progress-bar bg-danger';
                progressLbl.textContent  = 'Erro!';
                titleText.textContent    = 'SyncBridge \u2014 erro \u2716';

                appendLine(`<span class="log-error">\u2716  ${esc(event.msg)}</span>`);

                footer.className = '';
                footer.innerHTML =
                    '<div class="d-flex align-items-center gap-2 mb-2">'
                  + '  <span class="d-inline-flex align-items-center justify-content-center bg-danger text-white rounded-circle flex-shrink-0" style="width:36px;height:36px"><i class="bi bi-exclamation-triangle"></i></span>'
                  + '  <strong class="result-error fs-6">Erro na transfer\u00eancia</strong>'
                  + '</div>'
                  + '<p class="small mb-2" style="color:#f38ba8">' + esc(event.msg) + '</p>'
                  + '<button type="button" class="btn btn-outline-light btn-sm" onclick="window.goToStep(3)">'
                  + '  <i class="bi bi-arrow-left me-1"></i>Voltar e corrigir'
                  + '</button>';

                resetBtn();
            }
        }

        // ── SSE via fetch ReadableStream ────────────────────────
        fetch('/transfer/stream', {
            method: 'POST',
            body: new FormData(form),
        }).then(response => {
            if (!response.ok) throw new Error('HTTP ' + response.status);
            const reader  = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer    = '';

            function processChunk(value) {
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try { handleEvent(JSON.parse(line.slice(6))); }
                        catch (_) { /* ignore */ }
                    }
                }
            }

            function pump() {
                return reader.read().then(({ done, value }) => {
                    if (done) return;
                    processChunk(value);
                    return pump();
                });
            }

            return pump();

        }).catch(err => {
            appendLine(`<span class="log-error">\u2716  Erro de comunica\u00e7\u00e3o: ${esc(String(err))}</span>`);
            progressBar.className    = 'progress-bar bg-danger';
            progressBar.style.width  = '100%';
            progressLbl.textContent  = 'Erro de conex\u00e3o';
            resetBtn();
        });
    }

}());

// ── Connection String Builder — SQL Server ──────────────────────
(function () {
    let _targetInputId = null;
    let _csbModal = null;

    window.openConnStringBuilder = function (targetInputId) {
        _targetInputId = targetInputId;
        if (!_csbModal) {
            _csbModal = new bootstrap.Modal(document.getElementById('connStringBuilderModal'));
            document.getElementById('connStringBuilderModal').addEventListener('input', _updateCsbPreview);
            document.getElementById('connStringBuilderModal').addEventListener('change', _updateCsbPreview);
        }
        const current = document.getElementById(targetInputId).value.trim();
        // Reset form to defaults before populating
        document.getElementById('csb-server').value = '';
        document.getElementById('csb-port').value = '';
        document.getElementById('csb-database').value = '';
        document.getElementById('csb-uid').value = '';
        document.getElementById('csb-pwd').value = '';
        document.getElementById('csb-auth-sql').checked = true;
        document.getElementById('csb-encrypt').checked = false;
        document.getElementById('csb-trust-cert').checked = false;
        document.getElementById('csb-driver').selectedIndex = 0;
        if (current) _parseCsb(current);
        _updateCsbPreview();
        _csbModal.show();
    };

    function _parseCsb(str) {
        const get = function (key) {
            const m = str.match(new RegExp(key + '=([^;]+)', 'i'));
            return m ? m[1].trim() : '';
        };
        const driver = get('DRIVER').replace(/[{}]/g, '');
        const serverFull = get('SERVER');
        const parts = serverFull.split(',');
        document.getElementById('csb-server').value = parts[0] || '';
        document.getElementById('csb-port').value = parts[1] || '';
        document.getElementById('csb-database').value = get('DATABASE');
        const trusted = get('Trusted_Connection');
        if (trusted.toLowerCase() === 'yes') {
            document.getElementById('csb-auth-win').checked = true;
        } else {
            document.getElementById('csb-auth-sql').checked = true;
            document.getElementById('csb-uid').value = get('UID');
        }
        const driverSel = document.getElementById('csb-driver');
        for (let i = 0; i < driverSel.options.length; i++) {
            if (driverSel.options[i].value.toLowerCase() === driver.toLowerCase()) {
                driverSel.selectedIndex = i;
                break;
            }
        }
        document.getElementById('csb-encrypt').checked = /Encrypt=yes/i.test(str);
        document.getElementById('csb-trust-cert').checked = /TrustServerCertificate=yes/i.test(str);
    }

    function _toggleCsbAuth() {
        const isWin = document.getElementById('csb-auth-win').checked;
        document.getElementById('csb-sql-auth-fields').classList.toggle('d-none', isWin);
    }

    function _buildCsbString() {
        const driver    = document.getElementById('csb-driver').value;
        const server    = document.getElementById('csb-server').value.trim();
        const port      = document.getElementById('csb-port').value.trim();
        const database  = document.getElementById('csb-database').value.trim();
        const isWin     = document.getElementById('csb-auth-win').checked;
        const uid       = document.getElementById('csb-uid').value.trim();
        const pwd       = document.getElementById('csb-pwd').value;
        const encrypt   = document.getElementById('csb-encrypt').checked;
        const trustCert = document.getElementById('csb-trust-cert').checked;
        const serverStr = (server && port) ? server + ',' + port : server;
        let str = 'DRIVER={' + driver + '};';
        if (serverStr) str += 'SERVER=' + serverStr + ';';
        if (database)  str += 'DATABASE=' + database + ';';
        if (isWin) {
            str += 'Trusted_Connection=yes;';
        } else {
            if (uid) str += 'UID=' + uid + ';';
            if (pwd) str += 'PWD=' + pwd + ';';
        }
        if (encrypt)   str += 'Encrypt=yes;';
        if (trustCert) str += 'TrustServerCertificate=yes;';
        return str;
    }

    function _updateCsbPreview() {
        _toggleCsbAuth();
        const el = document.getElementById('csb-preview');
        if (el) el.textContent = _buildCsbString();
    }

    window.applyConnString = function () {
        if (_targetInputId) {
            document.getElementById(_targetInputId).value = _buildCsbString();
        }
        if (_csbModal) _csbModal.hide();
    };

    window.toggleCsbPassword = function () {
        const input = document.getElementById('csb-pwd');
        const icon  = document.getElementById('csb-pwd-eye');
        if (!input) return;
        if (input.type === 'password') {
            input.type = 'text';
            if (icon) icon.className = 'bi bi-eye-slash';
        } else {
            input.type = 'password';
            if (icon) icon.className = 'bi bi-eye';
        }
    };
}());

// ── Connection String Builder — Oracle DSN ──────────────────────
(function () {
    let _targetInputId = null;
    let _odbModal = null;

    window.openOracleDsnBuilder = function (targetInputId) {
        _targetInputId = targetInputId;
        if (!_odbModal) {
            _odbModal = new bootstrap.Modal(document.getElementById('oracleDsnBuilderModal'));
            document.getElementById('oracleDsnBuilderModal').addEventListener('input', _updateOdbPreview);
        }
        // Reset form before populating
        document.getElementById('odb-user').value = '';
        document.getElementById('odb-pwd').value = '';
        document.getElementById('odb-host').value = '';
        document.getElementById('odb-port').value = '1521';
        document.getElementById('odb-service').value = '';
        const current = document.getElementById(targetInputId).value.trim();
        if (current) _parseOdb(current);
        _updateOdbPreview();
        _odbModal.show();
    };

    function _parseOdb(str) {
        // Format: user/pass@host:port/service
        const m = str.match(/^([^/@]*)\/([^@]*)@([^:/]*):?(\d*)\/?(.*)?$/);
        if (m) {
            document.getElementById('odb-user').value    = m[1] || '';
            document.getElementById('odb-pwd').value     = m[2] || '';
            document.getElementById('odb-host').value    = m[3] || '';
            document.getElementById('odb-port').value    = m[4] || '1521';
            document.getElementById('odb-service').value = m[5] || '';
        }
    }

    function _buildOdbString() {
        const user    = document.getElementById('odb-user').value.trim();
        const pwd     = document.getElementById('odb-pwd').value;
        const host    = document.getElementById('odb-host').value.trim();
        const port    = document.getElementById('odb-port').value.trim() || '1521';
        const service = document.getElementById('odb-service').value.trim();
        return user + '/' + pwd + '@' + host + ':' + port + '/' + service;
    }

    function _updateOdbPreview() {
        const el = document.getElementById('odb-preview');
        if (el) el.textContent = _buildOdbString();
    }

    window.applyOracleDsn = function () {
        if (_targetInputId) {
            document.getElementById(_targetInputId).value = _buildOdbString();
        }
        if (_odbModal) _odbModal.hide();
    };

    window.toggleOdbPassword = function () {
        const input = document.getElementById('odb-pwd');
        const icon  = document.getElementById('odb-pwd-eye');
        if (!input) return;
        if (input.type === 'password') {
            input.type = 'text';
            if (icon) icon.className = 'bi bi-eye-slash';
        } else {
            input.type = 'password';
            if (icon) icon.className = 'bi bi-eye';
        }
    };
}());