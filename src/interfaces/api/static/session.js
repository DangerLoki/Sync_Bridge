// SyncBridge persistent web session + resumable transfer jobs.
(function () {
    'use strict';

    const ACTIVE_JOB_KEY = 'syncbridge.activeJobId';
    const FORM_STATE_KEY = 'syncbridge.formState';
    const STEP_KEY = 'syncbridge.currentStep';

    // Connection strings / DSNs may contain passwords. They are deliberately
    // not written to browser storage. Once a job starts, the server owns the
    // execution state and a refresh only needs the job id to reconnect.
    const SENSITIVE_FIELDS = new Set([
        'source_connection_string',
        'target_connection_string',
        'source_oracle_dsn',
        'target_oracle_dsn',
    ]);

    let currentJobId = null;
    let eventSource = null;
    let cancelButton = null;
    let terminalIsFinal = false;

    function esc(value) {
        const el = document.createElement('div');
        el.textContent = String(value == null ? '' : value);
        return el.innerHTML;
    }

    function ui() {
        return {
            form: document.getElementById('transfer-form'),
            terminal: document.getElementById('transfer-terminal'),
            output: document.getElementById('terminal-output'),
            progressBar: document.getElementById('terminal-progress-bar'),
            progressLabel: document.getElementById('terminal-progress-label'),
            rowsLabel: document.getElementById('terminal-rows-label'),
            footer: document.getElementById('terminal-result-footer'),
            title: document.getElementById('terminal-title-text'),
            runButton: document.getElementById('run-transfer-btn'),
        };
    }

    function appendLine(html) {
        const elements = ui();
        if (!elements.output) return;
        const span = document.createElement('span');
        span.innerHTML = html + '\n';
        elements.output.appendChild(span);
        elements.output.scrollTop = elements.output.scrollHeight;
    }

    function setRunButtonRunning(running) {
        const btn = ui().runButton;
        if (!btn) return;
        btn.disabled = running;
        btn.innerHTML = running
            ? '<span class="spinner-border spinner-border-sm me-2" style="width:.9rem;height:.9rem"></span>Transferindo...'
            : '<i class="bi bi-play-fill"></i> Executar transferência';
    }

    function setCancelVisible(visible, pending) {
        if (!cancelButton) return;
        cancelButton.classList.toggle('d-none', !visible);
        cancelButton.disabled = !!pending;
        cancelButton.innerHTML = pending
            ? '<span class="spinner-border spinner-border-sm me-1" style="width:.75rem;height:.75rem"></span>Cancelando...'
            : '<i class="bi bi-stop-circle me-1"></i>Cancelar';
    }

    function resetTerminal() {
        const elements = ui();
        terminalIsFinal = false;
        if (!elements.terminal) return;
        elements.output.innerHTML = '';
        elements.progressBar.style.width = '5%';
        elements.progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        elements.progressLabel.textContent = 'Conectando...';
        elements.rowsLabel.textContent = '';
        elements.footer.className = 'd-none';
        elements.footer.innerHTML = '';
        elements.title.textContent = 'SyncBridge — transferência em andamento';
        elements.terminal.classList.remove('d-none');
        setCancelVisible(true, false);
    }

    function prepareResumeTerminal() {
        resetTerminal();
        const elements = ui();
        elements.progressLabel.textContent = 'Reconectando à execução...';
        appendLine('<span class="log-start">↻  Sessão restaurada. Recuperando eventos da execução...</span>');
        if (window.goToStep) window.goToStep(3);
    }

    function formatRows(read, written) {
        return `${Number(read || 0).toLocaleString('pt-BR')} lidas · ${Number(written || 0).toLocaleString('pt-BR')} escritas`;
    }

    function finishCommon() {
        terminalIsFinal = true;
        setRunButtonRunning(false);
        setCancelVisible(false, false);
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    }

    function newTransferButtonHtml() {
        return '<button type="button" class="btn btn-outline-light btn-sm" id="session-new-transfer-btn">'
            + '<i class="bi bi-arrow-repeat me-1"></i>Nova transferência</button>';
    }

    function wireFooterButtons() {
        const newBtn = document.getElementById('session-new-transfer-btn');
        if (newBtn) {
            newBtn.addEventListener('click', function () {
                sessionStorage.removeItem(ACTIVE_JOB_KEY);
                currentJobId = null;
                terminalIsFinal = false;
                if (eventSource) eventSource.close();
                eventSource = null;
                const elements = ui();
                elements.terminal.classList.add('d-none');
                setRunButtonRunning(false);
                if (window.goToStep) window.goToStep(1);
            });
        }

        const retryBtn = document.getElementById('session-retry-transfer-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', function () {
                sessionStorage.removeItem(ACTIVE_JOB_KEY);
                currentJobId = null;
                terminalIsFinal = false;
                ui().terminal.classList.add('d-none');
                if (window.goToStep) window.goToStep(3);
            });
        }
    }

    function handleEvent(event) {
        const elements = ui();
        const ts = new Date().toLocaleTimeString('pt-BR', { hour12: false });

        if (event.type === 'log') {
            const level = event.level || 'info';
            const prefix = { debug: '·', info: '▸', warning: '⚠', error: '✖' }[level] || '▸';
            appendLine(`<span class="log-${esc(level)}">${ts}  ${prefix}  ${esc(event.msg)}</span>`);
            return;
        }

        if (event.type === 'start') {
            appendLine(`<span class="log-start">►  ${esc(event.msg)}</span>`);
            elements.progressLabel.textContent = 'Transferindo...';
            elements.progressBar.style.width = '15%';
            setRunButtonRunning(true);
            setCancelVisible(true, false);
            return;
        }

        if (event.type === 'progress') {
            elements.rowsLabel.textContent = formatRows(event.rows_read, event.rows_written);
            elements.progressLabel.textContent = event.done
                ? 'Finalizando...'
                : `Chunk ${Number(event.chunk_index || 0) + 1} processado`;
            return;
        }

        if (event.type === 'cancel_requested') {
            appendLine(`<span class="log-warning">⚠  ${esc(event.msg)}</span>`);
            elements.progressLabel.textContent = 'Cancelamento solicitado...';
            elements.title.textContent = 'SyncBridge — cancelando';
            setCancelVisible(true, true);
            return;
        }

        if (event.type === 'done') {
            elements.progressBar.style.width = '100%';
            elements.progressBar.className = 'progress-bar bg-success';
            elements.progressLabel.textContent = 'Concluído!';
            elements.rowsLabel.textContent = formatRows(event.rows_read, event.rows_written);
            elements.title.textContent = 'SyncBridge — concluído ✓';
            appendLine(`<span class="log-success">✔  Transferência concluída — ${Number(event.rows_read || 0).toLocaleString('pt-BR')} linhas lidas, ${Number(event.rows_written || 0).toLocaleString('pt-BR')} escritas.</span>`);

            elements.footer.className = '';
            elements.footer.innerHTML =
                '<div class="d-flex align-items-center gap-3 mb-3">'
                + '<span class="d-inline-flex align-items-center justify-content-center bg-success text-white rounded-circle flex-shrink-0" style="width:36px;height:36px"><i class="bi bi-check-lg"></i></span>'
                + '<strong class="result-success fs-6">Transferência concluída com sucesso</strong>'
                + '</div>'
                + '<div class="row g-2 small">'
                + `<div class="col-sm-6"><span class="text-secondary">Status:</span> <strong>${esc(event.status || 'SUCCESS')}</strong></div>`
                + `<div class="col-sm-6"><span class="text-secondary">Origem:</span> <strong>${esc(event.source)}</strong></div>`
                + `<div class="col-sm-6"><span class="text-secondary">Destino:</span> <strong>${esc(event.target)}</strong></div>`
                + `<div class="col-sm-6"><span class="text-secondary">Linhas lidas:</span> <strong>${Number(event.rows_read || 0).toLocaleString('pt-BR')}</strong></div>`
                + `<div class="col-sm-6"><span class="text-secondary">Linhas escritas:</span> <strong>${Number(event.rows_written || 0).toLocaleString('pt-BR')}</strong></div>`
                + '</div><div class="mt-3">' + newTransferButtonHtml() + '</div>';
            finishCommon();
            wireFooterButtons();
            return;
        }

        if (event.type === 'cancelled') {
            elements.progressBar.style.width = '100%';
            elements.progressBar.className = 'progress-bar bg-warning';
            elements.progressLabel.textContent = 'Cancelado';
            elements.rowsLabel.textContent = formatRows(event.rows_read, event.rows_written);
            elements.title.textContent = 'SyncBridge — cancelado';
            appendLine(`<span class="log-warning">■  ${esc(event.msg || 'Transferência cancelada.')}</span>`);

            const partial = event.partial_output
                ? '<p class="small mb-2 text-warning-emphasis">O destino pode conter dados parciais já gravados antes do cancelamento.</p>'
                : '';
            elements.footer.className = '';
            elements.footer.innerHTML =
                '<div class="d-flex align-items-center gap-2 mb-2">'
                + '<span class="d-inline-flex align-items-center justify-content-center bg-warning text-dark rounded-circle flex-shrink-0" style="width:36px;height:36px"><i class="bi bi-stop-fill"></i></span>'
                + '<strong class="fs-6">Transferência cancelada</strong></div>'
                + partial
                + '<div class="small mb-3">' + formatRows(event.rows_read, event.rows_written) + '</div>'
                + newTransferButtonHtml();
            finishCommon();
            wireFooterButtons();
            return;
        }

        if (event.type === 'error') {
            elements.progressBar.style.width = '100%';
            elements.progressBar.className = 'progress-bar bg-danger';
            elements.progressLabel.textContent = 'Erro!';
            elements.title.textContent = 'SyncBridge — erro ✖';
            appendLine(`<span class="log-error">✖  ${esc(event.msg)}</span>`);
            elements.footer.className = '';
            elements.footer.innerHTML =
                '<div class="d-flex align-items-center gap-2 mb-2">'
                + '<span class="d-inline-flex align-items-center justify-content-center bg-danger text-white rounded-circle flex-shrink-0" style="width:36px;height:36px"><i class="bi bi-exclamation-triangle"></i></span>'
                + '<strong class="result-error fs-6">Erro na transferência</strong></div>'
                + `<p class="small mb-2" style="color:#f38ba8">${esc(event.msg)}</p>`
                + '<button type="button" class="btn btn-outline-light btn-sm" id="session-retry-transfer-btn">'
                + '<i class="bi bi-arrow-left me-1"></i>Voltar e corrigir</button>';
            finishCommon();
            wireFooterButtons();
        }
    }

    function openStream(jobId) {
        if (eventSource) eventSource.close();
        eventSource = new EventSource(`/transfer/jobs/${encodeURIComponent(jobId)}/stream?after=0`);
        eventSource.onmessage = function (message) {
            try {
                handleEvent(JSON.parse(message.data));
            } catch (_) {
                // Ignore malformed event and keep the stream alive.
            }
        };
        eventSource.onerror = function () {
            if (terminalIsFinal) return;
            const elements = ui();
            elements.progressLabel.textContent = 'Reconectando...';
        };
    }

    async function cancelCurrentJob() {
        if (!currentJobId || terminalIsFinal) return;
        setCancelVisible(true, true);
        try {
            const response = await fetch(`/transfer/jobs/${encodeURIComponent(currentJobId)}/cancel`, {
                method: 'POST',
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
            if (!data.accepted && data.status) {
                ui().progressLabel.textContent = data.status === 'done' ? 'Concluído!' : data.status;
            }
        } catch (error) {
            appendLine(`<span class="log-error">✖  Não foi possível solicitar o cancelamento: ${esc(error)}</span>`);
            setCancelVisible(true, false);
        }
    }

    function injectCancelButton() {
        const copyButton = document.getElementById('terminal-copy-btn');
        if (!copyButton || document.getElementById('terminal-cancel-btn')) return;
        copyButton.classList.remove('ms-auto');
        cancelButton = document.createElement('button');
        cancelButton.type = 'button';
        cancelButton.id = 'terminal-cancel-btn';
        cancelButton.className = 'btn btn-outline-danger btn-sm ms-auto d-none py-0 px-2';
        cancelButton.innerHTML = '<i class="bi bi-stop-circle me-1"></i>Cancelar';
        cancelButton.title = 'Cancelar a transferência em andamento';
        cancelButton.addEventListener('click', cancelCurrentJob);
        copyButton.parentNode.insertBefore(cancelButton, copyButton);
    }

    function saveFormState() {
        const form = ui().form;
        if (!form) return;
        const state = {};
        Array.from(form.elements).forEach(function (field) {
            if (!field.name || SENSITIVE_FIELDS.has(field.name)) return;
            if (field.type === 'password' || field.type === 'file' || field.type === 'submit' || field.type === 'button') return;
            if (field.type === 'radio') {
                if (field.checked) state[field.name] = field.value;
                return;
            }
            if (field.type === 'checkbox') {
                state[field.name] = !!field.checked;
                return;
            }
            state[field.name] = field.value;
        });
        sessionStorage.setItem(FORM_STATE_KEY, JSON.stringify(state));
    }

    function restoreFormState() {
        const form = ui().form;
        if (!form) return;
        let state = null;
        try {
            state = JSON.parse(sessionStorage.getItem(FORM_STATE_KEY) || 'null');
        } catch (_) {
            state = null;
        }
        if (!state) return;

        Array.from(form.elements).forEach(function (field) {
            if (!field.name || !(field.name in state) || SENSITIVE_FIELDS.has(field.name)) return;
            const value = state[field.name];
            if (field.type === 'radio') field.checked = field.value === value;
            else if (field.type === 'checkbox') field.checked = !!value;
            else field.value = value;
        });

        ['source_type', 'target_type', 'enable_streaming'].forEach(function (id) {
            const element = document.getElementById(id);
            if (element) element.dispatchEvent(new Event('change', { bubbles: true }));
        });
    }

    function installWizardPersistence() {
        const originalGoToStep = window.goToStep;
        if (typeof originalGoToStep === 'function') {
            window.goToStep = function (step) {
                sessionStorage.setItem(STEP_KEY, String(step));
                return originalGoToStep(step);
            };
        }

        restoreFormState();
        const savedStep = parseInt(sessionStorage.getItem(STEP_KEY) || '1', 10);
        if (window.goToStep && savedStep >= 1 && savedStep <= 3) window.goToStep(savedStep);

        const form = ui().form;
        if (form) {
            form.addEventListener('input', saveFormState);
            form.addEventListener('change', saveFormState);
        }
    }

    async function startTransfer(event) {
        // This listener is registered in capture mode so the legacy streaming
        // handler in index.js does not start a second transfer.
        event.preventDefault();
        event.stopImmediatePropagation();

        const elements = ui();
        if (!elements.form || !elements.runButton) return;
        saveFormState();
        resetTerminal();
        setRunButtonRunning(true);
        if (window.goToStep) window.goToStep(3);
        elements.terminal.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        try {
            const response = await fetch('/transfer/jobs', {
                method: 'POST',
                body: new FormData(elements.form),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);

            currentJobId = data.job_id;
            sessionStorage.setItem(ACTIVE_JOB_KEY, currentJobId);
            openStream(currentJobId);
        } catch (error) {
            handleEvent({ type: 'error', msg: String(error) });
        }
    }

    async function resumeActiveJob() {
        const jobId = sessionStorage.getItem(ACTIVE_JOB_KEY);
        if (!jobId) return;

        try {
            const response = await fetch(`/transfer/jobs/${encodeURIComponent(jobId)}`);
            if (response.status === 404) {
                sessionStorage.removeItem(ACTIVE_JOB_KEY);
                return;
            }
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);

            currentJobId = jobId;
            prepareResumeTerminal();
            setRunButtonRunning(data.status === 'running' || data.status === 'cancelling');
            setCancelVisible(data.can_cancel, data.status === 'cancelling');
            openStream(jobId);
        } catch (error) {
            appendLine(`<span class="log-error">✖  Falha ao restaurar a execução: ${esc(error)}</span>`);
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        injectCancelButton();
        installWizardPersistence();

        const runButton = ui().runButton;
        if (runButton) runButton.addEventListener('click', startTransfer, true);

        resumeActiveJob();
    });
}());
