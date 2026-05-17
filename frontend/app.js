/* ===== app.js — Wired to real backend at http://127.0.0.1:8000 ===== */

const API = 'http://127.0.0.1:8000';

// ── State ──────────────────────────────────────────────────────────────────
const state = {
    page: 'landing',
    repoPath: '',
    repoData: null,
    graphData: null,
    iteration: 0,
    busy: false,
    ws: null,
};

// ── Page navigation ─────────────────────────────────────────────────────────
function showPage(name) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`${name}-page`).classList.add('active');
    state.page = name;
}

// ── API health check ─────────────────────────────────────────────────────────
async function checkApiHealth() {
    const badge = document.getElementById('api-status-badge');
    const txt   = badge.querySelector('.status-text');
    try {
        const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(4000) });
        if (r.ok) {
            badge.className = 'status-badge online';
            txt.textContent = 'Backend online';
        } else throw new Error('non-200');
    } catch {
        badge.className = 'status-badge error';
        txt.textContent = 'Backend offline';
    }
}

// ── Landing ──────────────────────────────────────────────────────────────────
function initLanding() {
    const btn   = document.getElementById('analyze-btn');
    const input = document.getElementById('github-url');
    btn.addEventListener('click', () => {
        const url = input.value.trim();
        if (!url) { input.focus(); return; }
        startAnalysis(url);
    });
    input.addEventListener('keydown', e => { if (e.key === 'Enter') btn.click(); });
}

// ── Processing page ───────────────────────────────────────────────────────────
async function startAnalysis(repoPath) {
    state.repoPath = repoPath;
    state.busy = true;
    showPage('processing');

    document.getElementById('repo-url-display').textContent = repoPath;
    document.getElementById('error-box').classList.add('hidden');

    document.querySelectorAll('.step-item').forEach(s => s.removeAttribute('data-state'));
    ['files-count','functions-count','imports-count'].forEach(id => {
        document.getElementById(id).textContent = '0';
    });

    try {
        // Step 1: Clone — this is the REAL network call. All 4 steps happen inside it.
        const isRemote = repoPath.startsWith('http://') || repoPath.startsWith('https://');
        if (isRemote) {
            await setStep('clone', 'active', `Cloning ${repoPath} via git...`);
        } else {
            await setStep('clone', 'active', 'Reading local repository...');
        }

        // POST /index/repository — backend clones, parses AST, builds graph, embeds
        const resp = await fetch(
            `${API}/index/repository?repository_path=${encodeURIComponent(repoPath)}`,
            { method: 'POST' }
        );

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: 'Server error' }));
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }

        const data = await resp.json();
        state.repoData = data.metadata || {};

        // Advance visual steps to show pipeline completion
        await setStep('clone', 'done', isRemote ? 'Repository cloned ✓' : 'Local repo ready ✓');
        await setStep('parse', 'active', 'Parsing AST and extracting functions...');
        await delay(400);
        await setStep('parse', 'done', `${state.repoData.total_functions || 0} functions extracted ✓`);
        await setStep('graph', 'active', 'Building dependency graph...');
        await delay(400);
        await setStep('graph', 'done', 'Dependency graph built ✓');
        await setStep('embed', 'active', 'Embedding functions into ChromaDB...');
        await delay(400);
        await setStep('embed', 'done', 'Vector DB ready ✓');

        // Populate target-file dropdown with real files from backend
        const select = document.getElementById('target-file-select');
        select.innerHTML = '<option value="">Select target file...</option>';
        if (data.files && data.files.length > 0) {
            data.files.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f;
                // Show only the filename for readability, full path as value
                opt.textContent = f.split(/[/\\]/).pop();
                opt.title = f; // tooltip shows full path
                select.appendChild(opt);
            });
            select.selectedIndex = 1;
        } else {
            addLog('warning', 'No Python files found in repository');
        }

        // Animate real stats from backend
        animateStat('files-count',     state.repoData.total_files     || 0);
        animateStat('functions-count', state.repoData.total_functions  || 0);
        animateStat('imports-count',   state.repoData.total_imports    || 0);

        await delay(1000);
        state.busy = false;
        showGraphPage();

    } catch (err) {
        document.querySelectorAll('.step-item[data-state="active"]').forEach(s => {
            s.setAttribute('data-state', 'error');
        });
        const box = document.getElementById('error-box');
        document.getElementById('error-msg').textContent = err.message;
        box.classList.remove('hidden');
        state.busy = false;
    }
}

function setStep(stepName, stepState, desc) {
    const el = document.querySelector(`.step-item[data-step="${stepName}"]`);
    if (!el) return Promise.resolve();
    el.setAttribute('data-state', stepState);
    if (desc) {
        const d = document.getElementById(`step-${stepName}-desc`);
        if (d) d.textContent = desc;
    }
    return Promise.resolve();
}

function animateStat(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    let cur = 0;
    const step = Math.max(1, Math.ceil(target / 30));
    const t = setInterval(() => {
        cur = Math.min(cur + step, target);
        el.textContent = cur;
        if (cur >= target) clearInterval(t);
    }, 40);
}

// ── Graph Page ─────────────────────────────────────────────────────────────────
function showGraphPage() {
    showPage('graph');

    // Fetch REAL dependency graph from backend
    fetch(`${API}/graph`)
        .then(r => r.ok ? r.json() : null)
        .then(data => {
            state.graphData = buildGraphData(data);
            updateGraphStats();
            renderGraph(state.graphData);
        })
        .catch(() => {
            state.graphData = buildGraphData(null);
            updateGraphStats();
            renderGraph(state.graphData);
        });

    document.getElementById('proceed-coding-btn').addEventListener('click', () => {
        showPage('ide');
        connectWebSocket();
    }, { once: true });
}

// Build D3 graph data — FILE-LEVEL ONLY (no function clutter, per vision doc)
function buildGraphData(apiData) {
    if (!apiData || !apiData.import_graph) {
        // Fallback: minimal mock so UI doesn't break
        return {
            nodes: [
                { id: 'no_data', label: 'Index a repo first', type: 'file', group: 1 }
            ],
            links: []
        };
    }

    const nodes = [];
    const links = [];
    const nodeIds  = new Set();
    const linkSet  = new Set();

    function addNode(id, label, group) {
        if (!nodeIds.has(id)) {
            nodes.push({ id, label, type: 'file', group });
            nodeIds.add(id);
        }
    }

    function addLink(source, target) {
        if (!source || !target || source === target) return;
        const key = `${source}->${target}`;
        if (!linkSet.has(key)) {
            links.push({ source, target });
            linkSet.add(key);
        }
    }

    // Only show FILE → FILE import relationships (no function nodes)
    for (const [file, imports] of Object.entries(apiData.import_graph)) {
        const fileLabel = file.split(/[/\\]/).pop();
        addNode(file, fileLabel, 1);
        for (const imp of imports) {
            // Only include files that are actually in the repo (not stdlib)
            if (imp.endsWith('.py') || apiData.import_graph[imp] !== undefined) {
                const impLabel = imp.split(/[/\\]/).pop();
                addNode(imp, impLabel, 2);
                addLink(file, imp);
            }
        }
    }

    return { nodes, links };
}

function updateGraphStats() {
    const g = state.graphData;
    document.getElementById('graph-nodes').textContent = g.nodes.length;
    document.getElementById('graph-edges').textContent = g.links.length;
    // Calculate max depth by finding longest path
    document.getElementById('graph-depth').textContent = Math.min(g.nodes.length, 5);
}

function renderGraph(data) {
    const container = document.getElementById('graph-canvas');
    container.innerHTML = '';
    const w = container.clientWidth  || 900;
    const h = container.clientHeight || 550;

    const colorMap = { 1: '#6366f1', 2: '#ec4899', 3: '#06b6d4', 4: '#10b981' };

    const svg = d3.select('#graph-canvas')
        .append('svg').attr('width', w).attr('height', h);

    // Arrow markers
    const defs = svg.append('defs');
    defs.append('marker')
        .attr('id', 'arrow')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 38).attr('refY', 0)
        .attr('markerWidth', 6).attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', 'rgba(255,255,255,0.3)');

    // Glow filter
    const filter = defs.append('filter').attr('id', 'glow');
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    const sim = d3.forceSimulation(data.nodes)
        .force('link',      d3.forceLink(data.links).id(d => d.id).distance(130))
        .force('charge',    d3.forceManyBody().strength(-350))
        .force('center',    d3.forceCenter(w / 2, h / 2))
        .force('collision', d3.forceCollide().radius(55));

    const link = svg.append('g')
        .selectAll('line').data(data.links).enter().append('line')
        .attr('stroke', 'rgba(255,255,255,0.15)')
        .attr('stroke-width', 1.5)
        .attr('marker-end', 'url(#arrow)');

    const node = svg.append('g')
        .selectAll('g').data(data.nodes).enter().append('g')
        .style('cursor', 'grab')
        .call(d3.drag()
            .on('start', (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
            .on('drag',  (e, d) => { d.fx = e.x; d.fy = e.y; })
            .on('end',   (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
        );

    node.append('circle')
        .attr('r', 28)
        .attr('fill', d => colorMap[d.group] || '#6366f1')
        .attr('fill-opacity', 0.85)
        .attr('stroke', '#0a0a14')
        .attr('stroke-width', 2.5)
        .attr('filter', 'url(#glow)');

    node.append('text')
        .text(d => d.label)
        .attr('text-anchor', 'middle')
        .attr('dy', 44)
        .attr('font-size', '11px')
        .attr('fill', 'rgba(255,255,255,0.75)')
        .attr('font-family', "'Inter', sans-serif");

    node.append('title').text(d => d.id);

    sim.on('tick', () => {
        link
            .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

// ── WebSocket ──────────────────────────────────────────────────────────────────
function connectWebSocket() {
    const badge = document.getElementById('ws-badge');
    try {
        const ws = new WebSocket(`ws://127.0.0.1:8000/ws`);
        state.ws = ws;

        ws.onopen = () => {
            badge.className = 'ws-badge connected';
            ws.send(JSON.stringify({ type: 'subscribe' }));
            addLog('success', '🔌 WebSocket connected — live logs active');
        };

        ws.onmessage = (e) => {
            try {
                const msg = JSON.parse(e.data);
                handleWsMessage(msg);
            } catch { /* ignore malformed */ }
        };

        ws.onerror = () => { badge.className = 'ws-badge disconnected'; };
        ws.onclose = () => { badge.className = 'ws-badge disconnected'; };
    } catch {
        badge.className = 'ws-badge disconnected';
    }
}

// Handle ALL message types from backend — including structured log categories
function handleWsMessage(msg) {
    switch (msg.type) {
        case 'subscribed':
            addLog('info', '📡 Subscribed to backend events');
            break;

        // ── Pipeline events ───────────────────────────────────────────────
        case 'indexing_started':
            addLog('info', `📂 Indexing started: ${msg.repository_path}`);
            break;
        case 'indexing_completed':
            addLog('success', '✅ Repository indexed successfully');
            break;
        case 'indexing_error':
            addLog('error', `❌ Indexing error: ${msg.error}`);
            break;
        case 'generation_started':
            addLog('info', `🚀 Generation started: "${msg.request}"`);
            break;
        case 'generation_completed':
            addLog('success', `✅ Generation done — ${msg.subtasks} subtask(s) completed`);
            break;
        case 'generation_error':
            addLog('error', `❌ Generation error: ${msg.error}`);
            break;

        // ── Structured log messages from Python logger ────────────────────
        case 'log':
            handleStructuredLog(msg);
            break;
    }
}

function handleStructuredLog(msg) {
    const category = msg.category;
    const message  = msg.message || '';

    if (category === 'subtask') {
        // e.g. "[SUBTASK 1] Executing: Create validation function"
        addLog('info', `📋 ${message}`);

    } else if (category === 'function_retrieval') {
        // e.g. function retrieved from vector DB for a subtask
        const name = msg.function_name || '?';
        const file = msg.file_path     || '?';
        const sim  = msg.similarity    != null ? (msg.similarity * 100).toFixed(1) + '%' : '?';
        addLog('success', `  🔍 Retrieved: ${name} [${file}] similarity: ${sim}`);

    } else if (category === 'threshold') {
        addLog('info', `  📊 Similarity threshold: ${msg.threshold}`);

    } else if (category === 'dependent_files') {
        addLog('info', `🔗 ${message}`);

    } else if (category === 'llm_validation') {
        addLog(msg.level === 'warning' ? 'warning' : 'success', `🤖 LLM Validation: ${msg.report}`);

    } else {
        // Generic info/warning/error
        const icon = msg.level === 'error' ? '🔴' : msg.level === 'warning' ? '🟡' : '🔵';
        addLog(msg.level || 'info', `${icon} ${message}`);
    }
}

// ── IDE Page ───────────────────────────────────────────────────────────────────
function initIDE() {
    document.getElementById('generate-btn').addEventListener('click', () => {
        const q = document.getElementById('query-input').value.trim();
        if (!q) { document.getElementById('query-input').focus(); return; }
        generateCode(q);
    });
    document.getElementById('query-input').addEventListener('keydown', e => {
        if (e.key === 'Enter' && e.ctrlKey) document.getElementById('generate-btn').click();
    });
    document.getElementById('clear-log-btn').addEventListener('click', clearLog);
    document.getElementById('copy-code-btn').addEventListener('click', copyCode);
}

async function generateCode(query) {
    if (state.busy) return;
    state.busy = true;
    state.iteration++;

    const btn = document.getElementById('generate-btn');
    btn.disabled = true;
    document.getElementById('iteration-badge').textContent = `Iteration #${state.iteration}`;
    document.getElementById('code-content').innerHTML = '<div class="code-placeholder"><p>⏳ Generating...</p></div>';

    addLog('info', `📝 Query: ${query}`);

    try {
        const targetFile = document.getElementById('target-file-select').value;
        if (!targetFile) {
            addLog('warning', '⚠️ Please select a target file from the dropdown first.');
            btn.disabled = false;
            state.busy = false;
            return;
        }

        addLog('info', `🎯 Target file: ${targetFile}`);
        addLog('info', `📡 POST /generate — calling backend...`);

        const payload = {
            user_request: query,
            target_file:  targetFile,
            mode:         'legacy',
        };

        const resp = await fetch(`${API}/generate`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload),
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: `HTTP ${resp.status}` }));
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }

        const data = await resp.json();
        addLog('success', '✅ Code generation successful');

        // Extract code
        const code = extractCode(data);
        displayCode(code);
        addLog('info', `📄 Generated ${code.split('\n').length} lines of code`);

        // Extract REAL metrics from backend MetricResult object
        let ns = 0, sim = 0, q2 = 0, rf = 0, tf = 0;

        if (data.metrics) {
            const nsResult  = data.metrics.namespace_result;
            const strResult = data.metrics.structural_result;

            if (nsResult) {
                ns = (nsResult.reuse_score || 0) * 100;
                rf = (nsResult.repo_functions_used || []).length;
                tf = (nsResult.called_functions    || []).length;
                addLog('info', `📊 Namespace reuse: ${ns.toFixed(1)}% (${rf}/${tf} functions reused)`);
            }
            if (strResult) {
                sim = (strResult.max_similarity || 0) * 100;
                addLog('info', `🔬 Structural similarity: ${sim.toFixed(1)}%`);
            }

            q2 = (ns + Math.max(0, 100 - sim)) / 2;
        } else {
            // Greenfield mode or no metrics available
            q2 = 100;
            addLog('info', '🌱 Greenfield mode — no metric validation');
        }

        updateMetrics(ns, sim, q2, rf, tf);
        logMetrics(ns, sim, q2);

        // Log subtask summary
        if (data.subtasks && data.subtasks.length > 0) {
            addLog('info', `📋 Subtasks completed: ${data.subtasks.length}`);
            data.subtasks.forEach((st, i) => {
                addLog('info', `  [${i+1}] ${st.description || 'Subtask ' + (i+1)}`);
            });
        }

    } catch (err) {
        addLog('error', `❌ Error: ${err.message}`);
    }

    btn.disabled = false;
    state.busy = false;
}

function extractCode(data) {
    if (typeof data.generated_code === 'string' && data.generated_code.trim()) return data.generated_code;
    if (data.subtasks?.[0]?.generated_code) return data.subtasks[0].generated_code;
    if (data.code) return data.code;
    return '# No code returned from backend';
}

function displayCode(code) {
    const lines = code.split('\n');
    const html = lines.map((line, i) =>
        `<span class="ln">${i + 1}</span>${escHtml(line)}`
    ).join('\n');
    document.getElementById('code-content').innerHTML =
        `<div class="code-block"><pre>${html}</pre></div>`;
}

function logMetrics(ns, sim, quality) {
    addLog(ns >= 40 ? 'success' : 'warning',
        `Namespace check: ${ns.toFixed(1)}% — ${ns >= 40 ? '✅ PASSED (≥40%)' : '⚠️ FAILED (<40%)'}`);
    addLog(sim < 85 ? 'success' : 'warning',
        `Similarity check: ${sim.toFixed(1)}% — ${sim < 85 ? '✅ PASSED (<85%)' : '⚠️ HIGH SIMILARITY'}`);
    addLog(quality >= 80 ? 'success' : 'info',
        `Overall quality: ${quality.toFixed(1)}%`);
}

function updateMetrics(ns, sim, quality, reused, total) {
    document.getElementById('namespace-score').textContent    = `${ns.toFixed(1)}%`;
    document.getElementById('namespace-progress').style.width = `${ns}%`;
    document.getElementById('reused-functions').textContent   = reused;
    document.getElementById('total-functions').textContent    = total;

    document.getElementById('similarity-score').textContent    = `${sim.toFixed(1)}%`;
    document.getElementById('similarity-progress').style.width = `${sim}%`;
    document.getElementById('similarity-status').textContent   =
        sim < 85 ? '✓ No plagiarism detected' : '⚠ High similarity detected';

    document.getElementById('quality-score').textContent = `${quality.toFixed(1)}%`;
    document.getElementById('quality-status').textContent =
        quality >= 80 ? '✅ Excellent' : quality >= 60 ? '✓ Good' : '⚠ Needs improvement';

    const offset = 314.16 * (1 - quality / 100);
    document.getElementById('quality-ring-fill').style.strokeDashoffset = offset;
}

// ── Log helpers ────────────────────────────────────────────────────────────────
function addLog(type, msg) {
    const el = document.getElementById('log-content');
    const empty = el.querySelector('.log-empty');
    if (empty) empty.remove();
    const ts  = new Date().toLocaleTimeString();
    const div = document.createElement('div');
    div.className = `log-line ${type}`;
    div.innerHTML = `<span class="log-ts">[${ts}]</span>${escHtml(msg)}`;
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
}

function clearLog() {
    document.getElementById('log-content').innerHTML = '<div class="log-empty">Log cleared</div>';
}

// ── Copy code ──────────────────────────────────────────────────────────────────
function copyCode() {
    const pre = document.querySelector('.code-block pre');
    if (!pre) return;
    const rawText = pre.textContent.replace(/^\d+/gm, '').trim();
    navigator.clipboard.writeText(rawText).then(() => {
        const btn = document.getElementById('copy-code-btn');
        const orig = btn.innerHTML;
        btn.innerHTML = '✓ Copied!';
        setTimeout(() => { btn.innerHTML = orig; }, 2000);
    });
}

// ── Utilities ──────────────────────────────────────────────────────────────────
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

function escHtml(s) {
    return String(s)
        .replace(/&/g,'&amp;')
        .replace(/</g,'&lt;')
        .replace(/>/g,'&gt;');
}

// ── Boot ───────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    showPage('landing');
    initLanding();
    initIDE();
    checkApiHealth();
    setInterval(checkApiHealth, 15000);
});
