/**
 * AI Data Cleaner - Frontend Application
 * =======================================
 * Handles all UI interactions and API calls
 */

// API Base URL
const API_BASE = '';

// State
let currentFile = null;
let currentDatasetId = null;

// DOM Elements
const elements = {
    // Views
    uploadView: document.getElementById('upload-view'),
    historyView: document.getElementById('history-view'),

    // Upload
    uploadZone: document.getElementById('upload-zone'),
    fileInput: document.getElementById('file-input'),
    uploadProgress: document.getElementById('upload-progress'),

    // Preview
    previewSection: document.getElementById('preview-section'),
    fileName: document.getElementById('file-name'),
    changeFileBtn: document.getElementById('change-file'),
    statRows: document.getElementById('stat-rows'),
    statCols: document.getElementById('stat-cols'),
    statDups: document.getElementById('stat-dups'),
    statMissing: document.getElementById('stat-missing'),
    previewTable: document.getElementById('preview-table'),
    validationIssues: document.getElementById('validation-issues'),
    issuesList: document.getElementById('issues-list'),

    // Clean
    cleanSection: document.getElementById('clean-section'),
    cleaningPrompt: document.getElementById('cleaning-prompt'),
    cleanBtn: document.getElementById('clean-btn'),
    suggestionTags: document.getElementById('suggestion-tags'),

    // Results
    resultsSection: document.getElementById('results-section'),
    resultRowsAfter: document.getElementById('result-rows-after'),
    resultRowsRemoved: document.getElementById('result-rows-removed'),
    resultParser: document.getElementById('result-parser'),
    actionsList: document.getElementById('actions-list'),
    cleanedTable: document.getElementById('cleaned-table'),
    exportBtn: document.getElementById('export-btn'),
    exportExcelBtn: document.getElementById('export-excel-btn'),
    exportFilename: document.getElementById('export-filename'),
    cleanAnotherBtn: document.getElementById('clean-another'),

    // History
    historyList: document.getElementById('history-list'),
    refreshHistoryBtn: document.getElementById('refresh-history'),

    // Loading & Toast
    loadingOverlay: document.getElementById('loading-overlay'),
    loadingText: document.getElementById('loading-text'),
    toastContainer: document.getElementById('toast-container'),
};

// ============================================================================
// NAVIGATION
// ============================================================================

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const view = btn.dataset.view;
        switchView(view);
    });
});

function switchView(view) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-view="${view}"]`).classList.add('active');

    // Update views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`${view}-view`).classList.add('active');

    // Load history if switching to history view
    if (view === 'history') {
        loadHistory();
    }
}

// ============================================================================
// FILE UPLOAD
// ============================================================================

// Click to upload
elements.uploadZone.addEventListener('click', () => {
    elements.fileInput.click();
});

// File selected
elements.fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        uploadFile(e.target.files[0]);
    }
});

// Drag and drop
elements.uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadZone.classList.add('dragover');
});

elements.uploadZone.addEventListener('dragleave', () => {
    elements.uploadZone.classList.remove('dragover');
});

elements.uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.uploadZone.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
});

async function uploadFile(file) {
    if (!file.name.endsWith('.csv')) {
        showToast('Please upload a CSV file', 'error');
        return;
    }

    // Show progress
    elements.uploadZone.classList.add('hidden');
    elements.uploadProgress.classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', file);

    try {
        showLoading('Uploading and analyzing file...');

        const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideLoading();

        if (data.error) {
            showToast(data.error, 'error');
            resetUpload();
            return;
        }

        // Success - show preview
        currentFile = data.filename;
        showPreview(data);
        showToast('File uploaded successfully!', 'success');

    } catch (error) {
        hideLoading();
        showToast('Upload failed: ' + error.message, 'error');
        resetUpload();
    }
}

function resetUpload() {
    elements.uploadZone.classList.remove('hidden');
    elements.uploadProgress.classList.add('hidden');
    elements.fileInput.value = '';
}

// Change file button
elements.changeFileBtn.addEventListener('click', () => {
    currentFile = null;
    elements.previewSection.classList.add('hidden');
    elements.cleanSection.classList.add('hidden');
    elements.resultsSection.classList.add('hidden');
    resetUpload();
});

// ============================================================================
// PREVIEW
// ============================================================================

function showPreview(data) {
    elements.uploadProgress.classList.add('hidden');
    elements.previewSection.classList.remove('hidden');
    elements.cleanSection.classList.remove('hidden');
    elements.resultsSection.classList.add('hidden');

    // File name
    elements.fileName.textContent = data.original_name;

    // Stats
    elements.statRows.textContent = data.info.rows.toLocaleString();
    elements.statCols.textContent = data.info.columns;
    elements.statDups.textContent = data.info.duplicate_rows;

    // Calculate total missing
    const totalMissing = Object.values(data.info.missing_counts).reduce((a, b) => a + b, 0);
    elements.statMissing.textContent = totalMissing.toLocaleString();

    // Render preview table
    renderTable(elements.previewTable, data.info.column_names, data.preview);

    // Show validation issues if any
    if (!data.validation.is_valid && data.validation.issues.length > 0) {
        elements.validationIssues.classList.remove('hidden');
        elements.issuesList.innerHTML = data.validation.issues
            .map(issue => `<li>${issue}</li>`)
            .join('');
    } else {
        elements.validationIssues.classList.add('hidden');
    }
}

function renderTable(tableElement, columns, rows) {
    const thead = tableElement.querySelector('thead');
    const tbody = tableElement.querySelector('tbody');

    // Header
    thead.innerHTML = `<tr>${columns.map(col => `<th>${col}</th>`).join('')}</tr>`;

    // Body
    if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="100%">No data</td></tr>';
    } else {
        tbody.innerHTML = rows.map(row =>
            `<tr>${columns.map(col => `<td>${row[col] ?? ''}</td>`).join('')}</tr>`
        ).join('');
    }
}

// ============================================================================
// CLEANING
// ============================================================================

// Suggestion tags
elements.suggestionTags.addEventListener('click', (e) => {
    if (e.target.classList.contains('suggestion-tag')) {
        const prompt = e.target.dataset.prompt;
        const current = elements.cleaningPrompt.value.trim();

        if (current) {
            elements.cleaningPrompt.value = current + ', ' + prompt.toLowerCase();
        } else {
            elements.cleaningPrompt.value = prompt;
        }

        elements.cleaningPrompt.focus();
    }
});

// Clean button
elements.cleanBtn.addEventListener('click', cleanData);

async function cleanData() {
    const prompt = elements.cleaningPrompt.value.trim();

    if (!prompt) {
        showToast('Please describe your cleaning task', 'error');
        return;
    }

    if (!currentFile) {
        showToast('Please upload a file first', 'error');
        return;
    }

    try {
        showLoading('Analyzing prompt and cleaning data...');

        const response = await fetch(`${API_BASE}/api/clean`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: currentFile,
                prompt: prompt
            })
        });

        const data = await response.json();
        hideLoading();

        if (data.error) {
            showToast(data.error, 'error');
            if (data.suggestions) {
                showToast('Try: ' + data.suggestions[0], 'info');
            }
            return;
        }

        // Save to IndexedDB (browser storage)
        try {
            const datasetId = await storage.saveDataset({
                filename: currentFile,
                originalFilename: currentFile,
                userPrompt: prompt,
                rules: data.rules_applied,
                parserUsed: data.parser_used,
                actionsLog: data.actions_log,
                stats: data.stats,
                cleanedData: data.preview, // Store the preview data
                columnNames: data.column_names
            });

            // Set the local dataset ID
            currentDatasetId = datasetId;
            console.log('✓ Saved to browser storage with ID:', datasetId);
        } catch (storageError) {
            console.error('Failed to save to browser storage:', storageError);
            showToast('Warning: Could not save to history', 'error');
        }

        // Success - show results
        showResults(data);
        showToast('Data cleaned successfully!', 'success');

    } catch (error) {
        hideLoading();
        showToast('Cleaning failed: ' + error.message, 'error');
    }
}

// ============================================================================
// RESULTS
// ============================================================================

function showResults(data) {
    elements.resultsSection.classList.remove('hidden');

    // Update export filename
    if (elements.exportFilename) {
        elements.exportFilename.textContent = `cleaned_dataset_${data.dataset_id}.csv`;
    }

    // Stats
    elements.resultRowsAfter.textContent = data.stats.rows_after.toLocaleString();
    elements.resultRowsRemoved.textContent = data.stats.rows_removed.toLocaleString();
    elements.resultParser.textContent = data.parser_used === 'gemini' ? 'AI (Gemini)' : 'Pattern Matching';

    // Actions log
    elements.actionsList.innerHTML = data.actions_log
        .map(action => `<li>${action}</li>`)
        .join('');

    // Cleaned data preview
    renderTable(elements.cleanedTable, data.column_names, data.preview);

    // Scroll to results
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Export CSV button
elements.exportBtn.addEventListener('click', async () => {
    if (!currentDatasetId) {
        showToast('No dataset to export', 'error');
        return;
    }

    try {
        window.location.href = `${API_BASE}/api/export/${currentDatasetId}`;
        showToast('CSV download started!', 'success');
    } catch (error) {
        showToast('Export failed: ' + error.message, 'error');
    }
});

// Export Excel button
if (elements.exportExcelBtn) {
    elements.exportExcelBtn.addEventListener('click', async () => {
        if (!currentDatasetId) {
            showToast('No dataset to export', 'error');
            return;
        }

        try {
            window.location.href = `${API_BASE}/api/export/${currentDatasetId}?format=excel`;
            showToast('Excel download started!', 'success');
        } catch (error) {
            showToast('Excel export failed: ' + error.message, 'error');
        }
    });
}

// Clean another button
elements.cleanAnotherBtn.addEventListener('click', () => {
    currentFile = null;
    currentDatasetId = null;
    elements.cleaningPrompt.value = '';
    elements.previewSection.classList.add('hidden');
    elements.cleanSection.classList.add('hidden');
    elements.resultsSection.classList.add('hidden');
    resetUpload();
});

// ============================================================================
// HISTORY
// ============================================================================

elements.refreshHistoryBtn.addEventListener('click', loadHistory);

async function loadHistory() {
    try {
        // Load from IndexedDB instead of server
        const datasets = await storage.getAllDatasets();
        renderHistory(datasets);

    } catch (error) {
        console.error('Failed to load history from browser storage:', error);
        showToast('Failed to load history: ' + error.message, 'error');
    }
}

function renderHistory(datasets) {
    if (!datasets || datasets.length === 0) {
        elements.historyList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <h3>No cleaning history yet</h3>
                <p>Upload and clean a CSV file to see it here</p>
            </div>
        `;
        return;
    }

    elements.historyList.innerHTML = datasets.map(ds => `
        <div class="history-item" data-id="${ds.id}">
            <div class="history-info">
                <h4>${ds.originalFilename || ds.filename}</h4>
                <p>
                    ${ds.stats?.rows_after || ds.stats?.rows_before || 'N/A'} rows • 
                    ${ds.parserUsed || 'Unknown'} parser • 
                    ${formatDate(ds.timestamp)}
                </p>
            </div>
            <div class="history-actions">
                <button class="btn btn-outline btn-sm" onclick="exportDataset(${ds.id})">
                    📥 Export
                </button>
                <button class="btn btn-outline btn-sm" onclick="deleteDataset(${ds.id})">
                    🗑️ Delete
                </button>
            </div>
        </div>
    `).join('');
}

function formatDate(dateStr) {
    if (!dateStr) return 'Unknown';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
        return dateStr;
    }
}

// Global functions for history actions
window.exportDataset = async function (id) {
    try {
        // Get dataset from IndexedDB
        const dataset = await storage.getDataset(id);

        if (!dataset) {
            showToast('Dataset not found', 'error');
            return;
        }

        // Convert cleaned data to CSV
        const csvContent = convertToCSV(dataset.cleanedData, dataset.columnNames);

        // Create download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', `cleaned_${dataset.filename}`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showToast('Download started!', 'success');
    } catch (error) {
        console.error('Export failed:', error);
        showToast('Export failed: ' + error.message, 'error');
    }
};

window.deleteDataset = async function (id) {
    if (!confirm('Are you sure you want to delete this dataset?')) return;

    try {
        await storage.deleteDataset(id);
        showToast('Dataset deleted', 'success');
        loadHistory();
    } catch (error) {
        console.error('Delete failed:', error);
        showToast('Delete failed: ' + error.message, 'error');
    }
};

// Helper function to convert data to CSV
function convertToCSV(data, columns) {
    if (!data || data.length === 0) return '';

    // Use provided columns or extract from first row
    const headers = columns || Object.keys(data[0]);

    // Create CSV header
    const csvRows = [headers.join(',')];

    // Add data rows
    for (const row of data) {
        const values = headers.map(header => {
            const value = row[header]?.toString() || '';
            // Escape quotes and wrap in quotes if contains comma or quote
            const escaped = value.replace(/"/g, '""');
            return escaped.includes(',') || escaped.includes('"') ? `"${escaped}"` : escaped;
        });
        csvRows.push(values.join(','));
    }

    return csvRows.join('\n');
}

// ============================================================================
// UTILITIES
// ============================================================================

function showLoading(text = 'Processing...') {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// ============================================================================
// INITIALIZATION
// ============================================================================

console.log('🧹 AI Data Cleaner loaded');
