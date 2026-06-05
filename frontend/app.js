const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000' : '';

let lastGeneratedSQL = '';

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

function setExample(text) {
    document.getElementById('nl-input').value = text;
    document.getElementById('nl-input').focus();
}

const BAD_SQL_EXAMPLES = {
    1: `SELECT *\nFROM customers\nWHERE YEAR(created_date) = 2024`,
    2: `SELECT customer_id, first_name, email\nFROM customers\nWHERE email LIKE '%@gmail.com'`,
    3: `SELECT first_name, last_name, email\nFROM customers\nWHERE customer_id NOT IN (\n    SELECT customer_id FROM orders WHERE status = 'completed'\n)`,
    4: `SELECT\n    c.first_name,\n    c.last_name,\n    COUNT(o.order_id) AS total_orders,\n    SUM(o.total_amount) AS lifetime_value\nFROM customers c\nLEFT JOIN orders o ON c.customer_id = o.customer_id\nGROUP BY c.customer_id, c.first_name, c.last_name\nORDER BY lifetime_value DESC\nLIMIT 10`
};

function setBadExample(num) {
    document.getElementById('sql-input').value = BAD_SQL_EXAMPLES[num];
    document.getElementById('sql-input').focus();
}

async function runNLQuery() {
    const question = document.getElementById('nl-input').value.trim();
    if (!question) { alert('Please enter a question.'); return; }

    const submitBtn = document.getElementById('nl-submit');
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').textContent = 'Working...';

    const resultsDiv = document.getElementById('nl-results');
    resultsDiv.innerHTML = `<div class="loading-state"><div class="spinner"></div><span>Generating SQL and fetching results...</span></div>`;
    resultsDiv.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/nl-to-sql`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'API error');
        }
        const data = await response.json();
        lastGeneratedSQL = data.generated_sql;
        resultsDiv.innerHTML = `
            <div class="card">
                <div class="card-header-row">
                    <h3 class="section-title">Generated SQL</h3>
                    <button class="copy-btn" onclick="copySQL()">Copy</button>
                </div>
                <pre class="sql-display" id="generated-sql">${escapeHtml(data.generated_sql)}</pre>
            </div>
            <div class="card">
                <div class="card-header-row">
                    <h3 class="section-title">SQL Quality Score</h3>
                    ${renderGradeBadge(data.analysis.grade, data.analysis.score)}
                </div>
                ${renderScoreBar(data.analysis.score)}
                ${renderIssues(data.analysis.issues)}
            </div>
            <div class="card">
                <div class="card-header-row">
                    <h3 class="section-title">Query Results</h3>
                    <span class="row-count-badge">${data.results.count} row${data.results.count !== 1 ? 's' : ''}</span>
                </div>
                ${data.results.error
                    ? `<p style="color:var(--accent-red);font-size:13px;">${escapeHtml(data.results.error)}</p>`
                    : renderTable(data.results)
                }
            </div>
            <div class="meta-row"><span class="meta-text">Completed in ${data.execution_time_ms}ms</span></div>
        `;
    } catch (error) {
        resultsDiv.innerHTML = `<div class="card" style="border-color:var(--accent-red)"><p style="color:var(--accent-red);font-weight:600;">Error</p><p style="color:var(--text-secondary);margin-top:8px;">${error.message}</p></div>`;
    } finally {
        submitBtn.disabled = false;
        submitBtn.querySelector('.btn-text').textContent = 'Generate SQL';
    }
}

async function analyzeSQL() {
    const sql = document.getElementById('sql-input').value.trim();
    if (!sql) { alert('Please paste a SQL query to analyze.'); return; }

    const submitBtn = document.getElementById('sql-submit');
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').textContent = 'Analyzing...';

    const resultsDiv = document.getElementById('analyzer-results');
    resultsDiv.innerHTML = `<div class="loading-state"><div class="spinner"></div><span>Analyzing query...</span></div>`;
    resultsDiv.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/analyze-sql`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql })
        });
        const data = await response.json();
        resultsDiv.innerHTML = `
            <div class="card">
                <div class="card-header-row">
                    <h3 class="section-title">Analysis Results</h3>
                    ${renderGradeBadge(data.grade, data.score)}
                </div>
                ${renderScoreBar(data.score)}
                ${renderIssues(data.issues)}
            </div>
        `;
    } catch (error) {
        resultsDiv.innerHTML = `<div class="card"><p style="color:var(--accent-red)">${error.message}</p></div>`;
    } finally {
        submitBtn.disabled = false;
        submitBtn.querySelector('.btn-text').textContent = 'Analyze Query';
    }
}

function renderGradeBadge(grade, score) {
    const colors = {
        'A': { bg: 'rgba(63,185,80,0.15)', color: '#3fb950', border: 'rgba(63,185,80,0.3)' },
        'B': { bg: 'rgba(88,166,255,0.15)', color: '#58a6ff', border: 'rgba(88,166,255,0.3)' },
        'C': { bg: 'rgba(240,136,62,0.15)', color: '#f0883e', border: 'rgba(240,136,62,0.3)' },
        'D': { bg: 'rgba(248,81,73,0.1)', color: '#f85149', border: 'rgba(248,81,73,0.3)' },
        'F': { bg: 'rgba(248,81,73,0.15)', color: '#f85149', border: 'rgba(248,81,73,0.5)' }
    };
    const c = colors[grade] || colors['F'];
    return `<div style="background:${c.bg};border:1px solid ${c.border};color:${c.color};width:42px;height:42px;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:20px;font-weight:700;">${grade}</div>`;
}

function renderScoreBar(score) {
    const color = score >= 90 ? '#3fb950' : score >= 70 ? '#f0883e' : '#f85149';
    return `<div class="score-bar-container">
        <div class="score-bar" style="--score-width:${score}%;--score-color:${color};"></div>
        <span class="score-label" style="color:${color};">${score}/100</span>
    </div>`;
}

function renderIssues(issues) {
    if (!issues || issues.length === 0) {
        return `<div class="no-issues">✅ No issues found — this query looks clean!</div>`;
    }
    return `<div class="issues-list">${issues.map(issue => `
        <div class="issue-item issue-${issue.severity}">
            <div class="issue-icon">${issue.severity === 'critical' ? '🔴' : issue.severity === 'warning' ? '🟡' : '🔵'}</div>
            <div class="issue-content">
                <div class="issue-code">${issue.code}</div>
                <div class="issue-message">${escapeHtml(issue.message)}</div>
                <div class="issue-fix"><strong>Fix:</strong> ${escapeHtml(issue.fix)}</div>
            </div>
        </div>`).join('')}
    </div>`;
}

function renderTable(results) {
    if (!results.columns || results.columns.length === 0) {
        return `<p style="color:var(--text-secondary);font-size:14px;">No results returned.</p>`;
    }
    const headers = results.columns.map(col => `<th>${escapeHtml(col)}</th>`).join('');
    const rows = results.rows.map(row =>
        `<tr>${results.columns.map(col => `<td>${escapeHtml(String(row[col] ?? 'NULL'))}</td>`).join('')}</tr>`
    ).join('');
    return `<div class="table-container">
        <table class="results-table">
            <thead><tr>${headers}</tr></thead>
            <tbody>${rows}</tbody>
        </table>
    </div>`;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function copySQL() {
    const sql = document.getElementById('generated-sql')?.textContent;
    if (sql) {
        navigator.clipboard.writeText(sql).then(() => {
            const btn = event.target;
            btn.textContent = 'Copied!';
            setTimeout(() => btn.textContent = 'Copy', 2000);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('nl-input').addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); runNLQuery(); }
    });
})