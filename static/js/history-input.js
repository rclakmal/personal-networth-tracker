// History Input Handler for Add Asset Modal
class HistoryInputHandler {
    constructor() {
        this.historyData = [];
        this.dateFormat = 'YYYY-MM-DD';
        this.currentMode = null;
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Mode switching buttons
        document.getElementById('paste-mode-btn')?.addEventListener('click', () => this.switchMode('paste'));
        document.getElementById('csv-upload-btn')?.addEventListener('click', () => this.switchMode('csv'));
        document.getElementById('manual-mode-btn')?.addEventListener('click', () => this.switchMode('manual'));

        // Date format selector
        document.getElementById('date-format-select')?.addEventListener('change', (e) => {
            this.dateFormat = e.target.value;
        });

        // Paste mode
        document.getElementById('parse-paste-btn')?.addEventListener('click', () => this.parsePasteData());

        // CSV upload
        document.getElementById('history-csv-file')?.addEventListener('change', (e) => this.handleCSVUpload(e));

        // Manual mode
        document.getElementById('add-history-row-btn')?.addEventListener('click', () => this.addManualRow());

        // Clear all
        document.getElementById('clear-history-btn')?.addEventListener('click', () => this.clearAllHistory());

        // Collapse/expand chevron
        document.getElementById('historySection')?.addEventListener('show.bs.collapse', () => {
            document.getElementById('history-chevron')?.classList.add('bi-chevron-down');
            document.getElementById('history-chevron')?.classList.remove('bi-chevron-right');
        });
        document.getElementById('historySection')?.addEventListener('hide.bs.collapse', () => {
            document.getElementById('history-chevron')?.classList.add('bi-chevron-right');
            document.getElementById('history-chevron')?.classList.remove('bi-chevron-down');
        });
    }

    switchMode(mode) {
        this.currentMode = mode;
        
        // Hide all sections
        document.getElementById('paste-mode-section').style.display = 'none';
        document.getElementById('csv-mode-section').style.display = 'none';
        document.getElementById('manual-mode-section').style.display = 'none';

        // Show selected section
        if (mode === 'paste') {
            document.getElementById('paste-mode-section').style.display = 'block';
        } else if (mode === 'csv') {
            document.getElementById('csv-mode-section').style.display = 'block';
        } else if (mode === 'manual') {
            document.getElementById('manual-mode-section').style.display = 'block';
            if (document.getElementById('history-manual-tbody').children.length === 0) {
                this.addManualRow();
            }
        }

        // Update button states
        document.querySelectorAll('.btn-group .btn').forEach(btn => btn.classList.remove('active'));
        event.target.closest('.btn').classList.add('active');
    }

    parsePasteData() {
        const textarea = document.getElementById('history-paste-area');
        const text = textarea.value.trim();
        
        if (!text) {
            alert('Please paste some data first.');
            return;
        }

        const lines = text.split('\n').filter(line => line.trim());
        const parsedData = [];
        const errors = [];

        lines.forEach((line, index) => {
            // Try different separators: tab, comma, space, semicolon
            let parts = line.split('\t').map(p => p.trim()).filter(p => p);
            
            if (parts.length < 2) {
                parts = line.split(',').map(p => p.trim()).filter(p => p);
            }
            if (parts.length < 2) {
                parts = line.split(';').map(p => p.trim()).filter(p => p);
            }
            if (parts.length < 2) {
                parts = line.split(/\s+/).filter(p => p);
            }

            if (parts.length >= 2) {
                const dateStr = parts[0];
                const valueStr = parts[1].replace(/,/g, ''); // Remove thousand separators
                
                const parsedDate = this.parseDate(dateStr);
                const parsedValue = parseFloat(valueStr);

                if (parsedDate && !isNaN(parsedValue)) {
                    parsedData.push({
                        date: parsedDate,
                        value: parsedValue,
                        originalDate: dateStr,
                        lineNumber: index + 1
                    });
                } else {
                    errors.push({
                        line: index + 1,
                        content: line,
                        reason: parsedDate ? 'Invalid value' : 'Invalid date'
                    });
                }
            } else {
                errors.push({
                    line: index + 1,
                    content: line,
                    reason: 'Could not split into date and value'
                });
            }
        });

        this.historyData = parsedData;
        this.updatePreview();
    }

    async handleCSVUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        const text = await file.text();
        const lines = text.split('\n').filter(line => line.trim());
        
        if (lines.length === 0) {
            alert('CSV file is empty.');
            return;
        }

        // Auto-detect if first line is header
        const firstLine = lines[0].toLowerCase();
        const hasHeader = firstLine.includes('date') || 
                         firstLine.includes('time') || 
                         firstLine.includes('value') || 
                         firstLine.includes('amount');

        const startIndex = hasHeader ? 1 : 0;
        const parsedData = [];
        const errors = [];

        for (let i = startIndex; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;

            const parts = line.split(',').map(p => p.trim());
            
            if (parts.length >= 2) {
                const dateStr = parts[0];
                const valueStr = parts[1].replace(/,/g, '');
                
                const parsedDate = this.parseDate(dateStr);
                const parsedValue = parseFloat(valueStr);

                if (parsedDate && !isNaN(parsedValue)) {
                    parsedData.push({
                        date: parsedDate,
                        value: parsedValue,
                        originalDate: dateStr,
                        lineNumber: i + 1
                    });
                } else {
                    errors.push({
                        line: i + 1,
                        content: line,
                        reason: parsedDate ? 'Invalid value' : 'Invalid date'
                    });
                }
            }
        }

        this.historyData = parsedData;
        this.updatePreview();
    }

    addManualRow(date = '', value = '') {
        const tbody = document.getElementById('history-manual-tbody');
        const row = document.createElement('tr');
        const rowId = Date.now();
        
        row.innerHTML = `
            <td>
                <input type="date" class="form-control form-control-sm" 
                       data-row-id="${rowId}" 
                       data-field="date"
                       value="${date}" 
                       max="${new Date().toISOString().split('T')[0]}">
            </td>
            <td>
                <input type="number" class="form-control form-control-sm" 
                       data-row-id="${rowId}" 
                       data-field="value"
                       value="${value}" 
                       step="0.01" 
                       placeholder="0.00">
            </td>
            <td>
                <button type="button" class="btn btn-sm btn-outline-danger" 
                        onclick="historyInputHandler.removeManualRow(this)">
                    <i class="bi bi-x"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);

        // Add change listeners
        row.querySelectorAll('input').forEach(input => {
            input.addEventListener('change', () => this.updateFromManualTable());
        });
    }

    removeManualRow(button) {
        button.closest('tr').remove();
        this.updateFromManualTable();
    }

    updateFromManualTable() {
        const tbody = document.getElementById('history-manual-tbody');
        const rows = tbody.querySelectorAll('tr');
        const parsedData = [];

        rows.forEach((row, index) => {
            const dateInput = row.querySelector('input[data-field="date"]');
            const valueInput = row.querySelector('input[data-field="value"]');
            
            if (dateInput.value && valueInput.value) {
                parsedData.push({
                    date: dateInput.value, // Already in YYYY-MM-DD format from date input
                    value: parseFloat(valueInput.value),
                    originalDate: dateInput.value,
                    lineNumber: index + 1
                });
            }
        });

        this.historyData = parsedData;
        this.updatePreview();
    }

    parseDate(dateStr) {
        if (!dateStr) return null;

        // Remove any quotes or extra whitespace
        dateStr = dateStr.replace(/['"]/g, '').trim();

        try {
            let year, month, day;

            if (this.dateFormat === 'YYYY-MM-DD') {
                // 2024-01-15 or 2024/01/15
                const match = dateStr.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/);
                if (match) {
                    year = parseInt(match[1], 10);
                    month = parseInt(match[2], 10);
                    day = parseInt(match[3], 10);
                }
            } else if (this.dateFormat === 'DD/MM/YYYY') {
                // 15/01/2024 or 15-01-2024
                const match = dateStr.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/);
                if (match) {
                    day = parseInt(match[1], 10);
                    month = parseInt(match[2], 10);
                    year = parseInt(match[3], 10);
                }
            } else if (this.dateFormat === 'MM/DD/YYYY') {
                // 01/15/2024 or 01-15-2024 or 8/28/2025
                const match = dateStr.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/);
                if (match) {
                    month = parseInt(match[1], 10);
                    day = parseInt(match[2], 10);
                    year = parseInt(match[3], 10);
                }
            } else if (this.dateFormat === 'DD-MM-YYYY') {
                // 15-01-2024
                const match = dateStr.match(/^(\d{1,2})[-](\d{1,2})[-](\d{4})$/);
                if (match) {
                    day = parseInt(match[1], 10);
                    month = parseInt(match[2], 10);
                    year = parseInt(match[3], 10);
                }
            }

            // Validate that we got all parts
            if (year && month && day) {
                // Validate ranges
                if (month < 1 || month > 12 || day < 1 || day > 31) {
                    return null;
                }

                // Create date object (month is 0-indexed in JavaScript Date)
                const date = new Date(year, month - 1, day);
                
                // Validate that the date is valid (e.g., not Feb 31)
                if (date.getFullYear() !== year || 
                    date.getMonth() !== month - 1 || 
                    date.getDate() !== day) {
                    return null;
                }

                // Check if date is not in the future
                const today = new Date();
                today.setHours(23, 59, 59, 999); // End of today
                
                if (date > today) {
                    return null; // Future date
                }

                // Return in YYYY-MM-DD format
                const paddedMonth = String(month).padStart(2, '0');
                const paddedDay = String(day).padStart(2, '0');
                return `${year}-${paddedMonth}-${paddedDay}`;
            }
        } catch (e) {
            return null;
        }

        return null;
    }

    updatePreview() {
        if (this.historyData.length === 0) {
            document.getElementById('history-preview-section').style.display = 'none';
            document.getElementById('history-count-badge').style.display = 'none';
            document.getElementById('history-data-hidden').value = '[]';
            return;
        }

        // Detect duplicates
        const dateMap = new Map();
        const duplicates = new Set();
        
        this.historyData.forEach(item => {
            if (dateMap.has(item.date)) {
                duplicates.add(item.date);
            }
            dateMap.set(item.date, item.value); // Last value wins
        });

        // Create deduplicated array (last value per date)
        const deduplicatedData = [];
        const seenDates = new Set();
        
        // Process in reverse to keep last occurrence
        for (let i = this.historyData.length - 1; i >= 0; i--) {
            const item = this.historyData[i];
            if (!seenDates.has(item.date)) {
                deduplicatedData.unshift(item);
                seenDates.add(item.date);
            }
        }

        // Sort by date
        deduplicatedData.sort((a, b) => a.date.localeCompare(b.date));

        // Show duplicate warning
        if (duplicates.size > 0) {
            document.getElementById('duplicate-warning').style.display = 'block';
            document.getElementById('duplicate-count').textContent = duplicates.size;
        } else {
            document.getElementById('duplicate-warning').style.display = 'none';
        }

        // Render preview table
        const tbody = document.getElementById('history-preview-tbody');
        tbody.innerHTML = '';

        deduplicatedData.forEach((item, index) => {
            const row = document.createElement('tr');
            const isDuplicate = duplicates.has(item.date);
            const isFuture = new Date(item.date) > new Date();
            
            let statusBadge = '<span class="badge bg-success">Valid</span>';
            let rowClass = 'history-row-valid';
            
            if (isFuture) {
                statusBadge = '<span class="badge bg-danger">Future Date</span>';
                rowClass = 'history-row-invalid';
            } else if (isDuplicate) {
                statusBadge = '<span class="badge bg-warning">Duplicate (last kept)</span>';
                rowClass = 'history-row-duplicate';
            }
            
            row.className = rowClass;
            row.innerHTML = `
                <td>${item.date}</td>
                <td>${item.value.toFixed(2)}</td>
                <td>${statusBadge}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-outline-danger" 
                            onclick="historyInputHandler.removePreviewRow('${item.date}')">
                        <i class="bi bi-x"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });

        // Update UI
        document.getElementById('history-preview-section').style.display = 'block';
        document.getElementById('preview-count').textContent = `(${deduplicatedData.length} entries)`;
        document.getElementById('history-count-badge').textContent = `${deduplicatedData.length} entries`;
        document.getElementById('history-count-badge').style.display = 'inline-block';

        // Store deduplicated data in hidden field
        document.getElementById('history-data-hidden').value = JSON.stringify(
            deduplicatedData.map(item => ({
                date: item.date,
                value: item.value
            }))
        );
    }

    removePreviewRow(date) {
        this.historyData = this.historyData.filter(item => item.date !== date);
        this.updatePreview();
    }

    clearAllHistory() {
        if (confirm('Are you sure you want to clear all historical data?')) {
            this.historyData = [];
            this.updatePreview();
            
            // Clear inputs
            document.getElementById('history-paste-area').value = '';
            document.getElementById('history-csv-file').value = '';
            document.getElementById('history-manual-tbody').innerHTML = '';
        }
    }

    getHistoryData() {
        const hiddenField = document.getElementById('history-data-hidden');
        return JSON.parse(hiddenField.value || '[]');
    }

    reset() {
        this.historyData = [];
        this.dateFormat = 'YYYY-MM-DD';
        this.currentMode = null;
        
        document.getElementById('history-paste-area').value = '';
        document.getElementById('history-csv-file').value = '';
        document.getElementById('history-manual-tbody').innerHTML = '';
        document.getElementById('date-format-select').value = 'YYYY-MM-DD';
        
        this.updatePreview();
        
        // Hide all mode sections
        document.getElementById('paste-mode-section').style.display = 'none';
        document.getElementById('csv-mode-section').style.display = 'none';
        document.getElementById('manual-mode-section').style.display = 'none';
        
        // Reset button states
        document.querySelectorAll('.btn-group .btn').forEach(btn => btn.classList.remove('active'));
    }
}

// Initialize global instance
document.addEventListener('DOMContentLoaded', function() {
    window.historyInputHandler = new HistoryInputHandler();
});
