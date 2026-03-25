'use strict';

const LEVEL_HEIGHT  = 150;
const NODE_RADIUS   = 22;
const LABEL_WIDTH   = 120;

const COLOR_AXIOM   = '#4a90d9';
const COLOR_THEOREM = '#e8a838';
const COLOR_ACTIVE  = '#e05555';

// ── i18n ──────────────────────────────────────────────────────────
let currentLang = localStorage.getItem('lang') || 'ru';

const STRINGS = {
  en: { axiom: 'Axiom', theorem: 'Theorem', hint: 'Click a node to view the proof', search: 'Search\u2026' },
  ru: { axiom: 'Аксиома', theorem: 'Теорема', hint: 'Нажмите на узел, чтобы увидеть доказательство', search: 'Поиск\u2026' },
};

function t(key) {
  return (STRINGS[currentLang] || STRINGS.en)[key];
}

function getTitle(d) {
  return d.title[currentLang] || d.title.en || d.title.ru || d.slug;
}

function getDescription(d) {
  return d.description[currentLang] || d.description.en || d.description.ru || '';
}

function applyI18n() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  document.getElementById('lang-en').classList.toggle('active', currentLang === 'en');
  document.getElementById('lang-ru').classList.toggle('active', currentLang === 'ru');
  const si = document.getElementById('search-input');
  if (si) si.placeholder = t('search');
}

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  applyI18n();
  fetch('/api/graph/')
    .then(r => r.json())
    .then(initGraph);
});

function initGraph(data) {
  const container = document.getElementById('graph-container');
  const svg       = d3.select('#graph-svg');
  const width     = container.clientWidth;
  const height    = container.clientHeight;

  const nodeBySlug = new Map(data.nodes.map(n => [n.slug, n]));

  function levelY(level) {
    const padding = 80;
    return height - padding - level * LEVEL_HEIGHT;
  }

  // ── Arrowhead markers ─────────────────────────────────────────
  const defs = svg.append('defs');

  defs.append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', NODE_RADIUS + 10)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#5a5f78');

  defs.append('marker')
    .attr('id', 'arrowhead-active')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', NODE_RADIUS + 10)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', COLOR_ACTIVE);

  const mainGroup = svg.append('g').attr('class', 'main');

  // ── Zoom & pan ────────────────────────────────────────────────
  svg.call(
    d3.zoom()
      .scaleExtent([0.3, 3])
      .on('zoom', e => mainGroup.attr('transform', e.transform))
  );

  // ── Edges ─────────────────────────────────────────────────────
  const edgeGroup = mainGroup.append('g').attr('class', 'edges');

  const edgeSel = edgeGroup.selectAll('line.edge')
    .data(data.edges)
    .join('line')
      .attr('class', 'edge')
      .attr('marker-end', 'url(#arrowhead)');

  // ── Nodes ─────────────────────────────────────────────────────
  const nodeGroup = mainGroup.append('g').attr('class', 'nodes');

  // Spread nodes horizontally within each level for a clean initial layout
  const nodesByLevel = new Map();
  data.nodes.forEach(n => {
    if (!nodesByLevel.has(n.level)) nodesByLevel.set(n.level, []);
    nodesByLevel.get(n.level).push(n);
  });

  const nodeData = data.nodes.map(n => {
    const lvlNodes = nodesByLevel.get(n.level);
    const idx   = lvlNodes.indexOf(n);
    const count = lvlNodes.length;
    // Give each node ~140px horizontal space so they don't overlap on start
    const neededWidth = count * 140;
    const spread = Math.max(neededWidth, width * 0.6);
    const startX = (width - spread) / 2;
    return {
      ...n,
      x:  count > 1 ? startX + (idx / (count - 1)) * spread : width / 2,
      fy: levelY(n.level),
    };
  });

  const nodeSel = nodeGroup.selectAll('g.node')
    .data(nodeData, d => d.id)
    .join('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', dragStart)
        .on('drag',  dragged)
        .on('end',   dragEnd)
      )
      .on('click', (event, d) => { event.stopPropagation(); openPanel(d); });

  nodeSel.append('circle')
    .attr('r', NODE_RADIUS)
    .attr('fill', d => d.node_type === 'axiom' ? COLOR_AXIOM : COLOR_THEOREM);

  function renderNodeLabel(sel, d) {
    sel.selectAll('foreignObject').remove();

    const fo = sel.append('foreignObject')
      .attr('x', -LABEL_WIDTH / 2)
      .attr('y', NODE_RADIUS + 6)
      .attr('width', LABEL_WIDTH)
      .attr('height', 80);

    const div = fo.append('xhtml:div')
      .attr('class', 'node-label')
      .text(getTitle(d));

    renderMathInElement(div.node(), {
      delimiters: [
        { left: '$$', right: '$$', display: true  },
        { left: '$',  right: '$',  display: false },
      ],
      throwOnError: false,
    });
  }

  nodeSel.each(function(d) { renderNodeLabel(d3.select(this), d); });

  // ── Force simulation ──────────────────────────────────────────
  const linkForce = d3.forceLink(data.edges)
    .id(d => d.id)
    .distance(LEVEL_HEIGHT)
    .strength(0.08);

  const simulation = d3.forceSimulation(nodeData)
    .force('link',    linkForce)
    .force('charge',  d3.forceManyBody().strength(-350))
    .force('collide', d3.forceCollide(NODE_RADIUS + 50))
    .force('x',       d3.forceX(width / 2).strength(0.04))
    .alpha(0.3)
    .alphaDecay(0.03)
    .on('tick', ticked);

  function ticked() {
    edgeSel
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.fy)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.fy);

    nodeSel.attr('transform', d => `translate(${d.x},${d.fy})`);
  }

  // ── Drag handlers ─────────────────────────────────────────────
  let didDrag = false;

  function dragStart(event, d) {
    didDrag = false;
    d.fx = d.x;
  }

  function dragged(event, d) {
    if (!didDrag) {
      didDrag = true;
      if (!event.active) simulation.alphaTarget(0.3).restart();
    }
    d.fx = event.x;
  }

  function dragEnd(event, d) {
    if (didDrag && !event.active) simulation.alphaTarget(0);
    d.fx = null;
  }

  // ── Active node highlight ─────────────────────────────────────
  let activeNodeId = null;

  function nodeColor(n) {
    return n.node_type === 'axiom' ? COLOR_AXIOM : COLOR_THEOREM;
  }

  function setActiveNode(d) {
    if (!d) {
      activeNodeId = null;
      nodeSel.select('circle')
        .attr('fill', nodeColor)
        .style('opacity', 1);
      nodeSel.select('foreignObject').style('opacity', 1);
      edgeSel
        .attr('stroke', '#3a3d4f')
        .attr('stroke-width', 1.5)
        .attr('marker-end', 'url(#arrowhead)')
        .style('opacity', 1);
      return;
    }

    if (activeNodeId === d.id) return;

    activeNodeId = d.id;

    // Find directly connected nodes
    const preds = new Set();
    const succs = new Set();
    data.edges.forEach(e => {
      const sid = typeof e.source === 'object' ? e.source.id : e.source;
      const tid = typeof e.target === 'object' ? e.target.id : e.target;
      if (tid === d.id) preds.add(sid);
      if (sid === d.id) succs.add(tid);
    });
    const connected = new Set([...preds, ...succs, d.id]);

    function isEdgeConnected(e) {
      const sid = typeof e.source === 'object' ? e.source.id : e.source;
      const tid = typeof e.target === 'object' ? e.target.id : e.target;
      return sid === d.id || tid === d.id;
    }

    // Dim / highlight nodes
    nodeSel.select('circle')
      .attr('fill', n => n.id === d.id ? COLOR_ACTIVE : nodeColor(n))
      .style('opacity', n => connected.has(n.id) ? 1 : 0.12);

    nodeSel.select('foreignObject')
      .style('opacity', function(n) {
        return connected.has(n.id) ? 1 : 0.12;
      });

    // Dim / highlight edges — connected ones turn red and thick
    edgeSel.each(function(e) {
      const active = isEdgeConnected(e);
      d3.select(this)
        .attr('stroke',       active ? COLOR_ACTIVE : '#3a3d4f')
        .attr('stroke-width', active ? 3 : 1)
        .attr('marker-end',   active ? 'url(#arrowhead-active)' : 'url(#arrowhead)')
        .style('opacity',     active ? 1 : 0.06);
    });
  }

  // ── Proof panel ───────────────────────────────────────────────
  const panel      = document.getElementById('proof-panel');
  const panelTitle = document.getElementById('panel-title');
  const panelBadge = document.getElementById('panel-type-badge');
  const panelBody  = document.getElementById('panel-body');
  const closeBtn   = document.getElementById('panel-close');

  closeBtn.addEventListener('click', closePanel);

  panelBody.addEventListener('click', e => {
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;
    e.preventDefault();
    const slug   = link.getAttribute('href').slice(1);
    const target = nodeBySlug.get(slug);
    if (target) openPanel(target);
  });

  let activePanelNode = null;

  function openPanel(d) {
    const wasOpen = panel.classList.contains('open');
    activePanelNode = d;

    // Open panel FIRST (before highlight) so the slide-in transition
    // doesn't cause a reflow that flickers the graph
    if (!wasOpen) panel.classList.add('open');

    const title = getTitle(d);
    panelTitle.textContent  = title.replace(/\$[^$]*\$/g, '').trim();
    panelBadge.textContent  = t(d.node_type);
    panelBadge.className    = 'panel-type-badge ' + d.node_type;
    panelBadge.id           = 'panel-type-badge';

    panelBody.innerHTML = marked.parse(getDescription(d));
    renderMathInElement(panelBody, {
      delimiters: [
        { left: '$$', right: '$$', display: true  },
        { left: '$',  right: '$',  display: false },
      ],
      throwOnError: false,
    });

    // Apply highlight AFTER panel content is set, in next frame
    // to avoid the panel slide-in transition causing reflow flicker
    if (!wasOpen) {
      requestAnimationFrame(() => setActiveNode(d));
    } else {
      setActiveNode(d);
    }

    const hint = document.getElementById('hint');
    if (hint) hint.style.opacity = '0';
  }

  function closePanel() {
    activePanelNode = null;
    setActiveNode(null);
    panel.classList.remove('open');
  }

  // ── Language switcher ─────────────────────────────────────────
  function switchLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('lang', lang);
    applyI18n();
    nodeSel.each(function(d) { renderNodeLabel(d3.select(this), d); });
    if (activePanelNode) openPanel(activePanelNode);
  }

  document.getElementById('lang-en').addEventListener('click', () => switchLanguage('en'));
  document.getElementById('lang-ru').addEventListener('click', () => switchLanguage('ru'));

  // ── Search ───────────────────────────────────────────────────
  const searchInput   = document.getElementById('search-input');
  const searchResults = document.getElementById('search-results');

  function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function stripLatex(s) {
    return s.replace(/\$\$[^$]*\$\$/g, ' ').replace(/\$[^$]*\$/g, ' ').replace(/\\[a-zA-Z]+/g, '');
  }

  function extractSnippet(text, query, maxLen) {
    const lower = text.toLowerCase();
    const idx = lower.indexOf(query);
    if (idx === -1) return '';
    const start = Math.max(0, idx - 30);
    const end = Math.min(text.length, idx + query.length + maxLen);
    let snippet = text.slice(start, end).trim();
    if (start > 0) snippet = '\u2026' + snippet;
    if (end < text.length) snippet += '\u2026';
    return snippet;
  }

  function highlightSearchMatches(matchIds) {
    if (!matchIds || !matchIds.size) {
      nodeSel.select('circle').attr('fill', nodeColor).style('opacity', 1);
      nodeSel.select('foreignObject').style('opacity', 1);
      edgeSel
        .attr('stroke', '#3a3d4f').attr('stroke-width', 1.5)
        .attr('marker-end', 'url(#arrowhead)').style('opacity', 1);
      return;
    }
    nodeSel.select('circle')
      .attr('fill', nodeColor)
      .style('opacity', n => matchIds.has(n.id) ? 1 : 0.1);
    nodeSel.select('foreignObject').style('opacity', n => matchIds.has(n.id) ? 1 : 0.1);
    edgeSel
      .attr('stroke', '#3a3d4f').attr('stroke-width', 1)
      .attr('marker-end', 'url(#arrowhead)').style('opacity', 0.05);
  }

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    if (q.length < 2) {
      searchResults.style.display = 'none';
      if (!activeNodeId) highlightSearchMatches(null);
      return;
    }

    const allMatches = data.nodes.filter(n => {
      const title = stripLatex(getTitle(n)).toLowerCase();
      const desc  = stripLatex(getDescription(n)).toLowerCase();
      return title.includes(q) || desc.includes(q);
    });

    // Выделяем ВСЕ подходящие на графе
    highlightSearchMatches(new Set(allMatches.map(n => n.id)));

    // В dropdown — только первые 8
    const matches = allMatches.slice(0, 8);
    if (!matches.length) { searchResults.style.display = 'none'; return; }

    searchResults.innerHTML = matches.map(n => {
      const title = getTitle(n);
      const desc  = getDescription(n);
      const snippet = extractSnippet(stripLatex(desc), q, 60);
      const badge = t(n.node_type);
      return `<div class="search-item" data-slug="${n.slug}">
        <span class="search-item-badge ${n.node_type}">${escapeHtml(badge)}</span>
        <span class="search-item-title">${escapeHtml(title)}</span>
        ${snippet ? `<div class="search-item-snippet">${escapeHtml(snippet)}</div>` : ''}
      </div>`;
    }).join('');
    searchResults.style.display = 'block';
  });

  searchResults.addEventListener('click', e => {
    const item = e.target.closest('.search-item');
    if (!item) return;
    const node = nodeData.find(n => n.slug === item.dataset.slug);
    searchResults.style.display = 'none';
    searchInput.value = '';
    if (node) openPanel(node);  // setActiveNode handles highlighting
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('.search-wrapper')) {
      searchResults.style.display = 'none';
    }
  });

  searchInput.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      searchInput.value = '';
      searchResults.style.display = 'none';
      highlightSearchMatches(null);
      searchInput.blur();
    }
  });

  // ── Responsive resize ─────────────────────────────────────────
  window.addEventListener('resize', () => {
    const w = container.clientWidth;
    simulation.force('x', d3.forceX(w / 2).strength(0.04));
    nodeData.forEach(n => { n.fy = levelY(n.level); });
    simulation.alpha(0.3).restart();
  });
}
