'use strict';

const LEVEL_HEIGHT  = 150;
const NODE_RADIUS   = 22;
const LABEL_WIDTH   = 120;

const COLOR_AXIOM   = '#4a90d9';
const COLOR_THEOREM = '#e8a838';
const COLOR_ACTIVE  = '#e05555';

document.addEventListener('DOMContentLoaded', () => {
  fetch('/api/graph/')
    .then(r => r.json())
    .then(initGraph);
});

function initGraph(data) {
  const container = document.getElementById('graph-container');
  const svg       = d3.select('#graph-svg');
  const width     = container.clientWidth;
  const height    = container.clientHeight;

  // Slug → node datum lookup for cross-reference links
  const nodeBySlug = new Map(data.nodes.map(n => [n.slug, n]));

  function levelY(level) {
    const padding = 80;
    return height - padding - level * LEVEL_HEIGHT;
  }

  // ── Arrowhead marker ──────────────────────────────────────────
  svg.append('defs').append('marker')
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

  const nodeData = data.nodes.map(n => ({
    ...n,
    x:  width / 2,
    fy: levelY(n.level),
  }));

  const nodeSel = nodeGroup.selectAll('g.node')
    .data(nodeData, d => d.id)
    .join('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', dragStart)
        .on('drag',  dragged)
        .on('end',   dragEnd)
      )
      .on('click', (event, d) => openPanel(d));

  nodeSel.append('circle')
    .attr('r', NODE_RADIUS)
    .attr('fill', d => d.node_type === 'axiom' ? COLOR_AXIOM : COLOR_THEOREM);

  // Labels via foreignObject so KaTeX renders and CSS wraps text
  nodeSel.each(function(d) {
    const fo = d3.select(this).append('foreignObject')
      .attr('x', -LABEL_WIDTH / 2)
      .attr('y', NODE_RADIUS + 6)
      .attr('width', LABEL_WIDTH)
      .attr('height', 80);

    const div = fo.append('xhtml:div')
      .attr('class', 'node-label')
      .text(d.title);

    renderMathInElement(div.node(), {
      delimiters: [
        { left: '$$', right: '$$', display: true  },
        { left: '$',  right: '$',  display: false },
      ],
      throwOnError: false,
    });
  });

  // ── Force simulation ──────────────────────────────────────────
  const linkForce = d3.forceLink(data.edges)
    .id(d => d.id)
    .distance(LEVEL_HEIGHT * 0.85)
    .strength(0.3);

  const simulation = d3.forceSimulation(nodeData)
    .force('link',    linkForce)
    .force('charge',  d3.forceManyBody().strength(-600))
    .force('collide', d3.forceCollide(NODE_RADIUS + 55))
    .force('x',       d3.forceX(width / 2).strength(0.06))
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
  function dragStart(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
  }

  function dragged(event, d) {
    d.fx = event.x;
  }

  function dragEnd(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
  }

  // ── Active node highlight ─────────────────────────────────────
  let activeNodeId = null;

  function setActiveNode(d) {
    // Restore previous
    if (activeNodeId !== null) {
      nodeSel.filter(n => n.id === activeNodeId)
        .select('circle')
        .attr('fill', n => n.node_type === 'axiom' ? COLOR_AXIOM : COLOR_THEOREM);
    }
    // Highlight new
    activeNodeId = d ? d.id : null;
    if (d) {
      nodeSel.filter(n => n.id === d.id)
        .select('circle')
        .attr('fill', COLOR_ACTIVE);
    }
  }

  // ── Proof panel ───────────────────────────────────────────────
  const panel      = document.getElementById('proof-panel');
  const panelTitle = document.getElementById('panel-title');
  const panelBadge = document.getElementById('panel-type-badge');
  const panelBody  = document.getElementById('panel-body');
  const closeBtn   = document.getElementById('panel-close');

  closeBtn.addEventListener('click', closePanel);

  // Intercept clicks on cross-reference links inside proof text
  panelBody.addEventListener('click', e => {
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;
    e.preventDefault();
    const slug   = link.getAttribute('href').slice(1);
    const target = nodeBySlug.get(slug);
    if (target) openPanel(target);
  });

  function nodeColor(n) {
    return n.node_type === 'axiom' ? COLOR_AXIOM : COLOR_THEOREM;
  }

  function openPanel(d) {
    setActiveNode(d);

    panelTitle.textContent  = d.title.replace(/\$[^$]*\$/g, '').trim();
    panelBadge.textContent  = d.node_type === 'axiom' ? 'Аксиома' : 'Теорема';
    panelBadge.className    = 'panel-type-badge ' + d.node_type;
    panelBadge.id           = 'panel-type-badge';

    panelBody.innerHTML = marked.parse(d.description);
    renderMathInElement(panelBody, {
      delimiters: [
        { left: '$$', right: '$$', display: true  },
        { left: '$',  right: '$',  display: false },
      ],
      throwOnError: false,
    });

    panel.classList.add('open');

    const hint = document.getElementById('hint');
    if (hint) hint.style.opacity = '0';
  }

  function closePanel() {
    setActiveNode(null);
    panel.classList.remove('open');
  }

  // ── Responsive resize ─────────────────────────────────────────
  window.addEventListener('resize', () => {
    const w = container.clientWidth;
    simulation.force('x', d3.forceX(w / 2).strength(0.06));
    nodeData.forEach(n => { n.fy = levelY(n.level); });
    simulation.alpha(0.3).restart();
  });
}
