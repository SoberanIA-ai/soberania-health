/* global React */
const { useState, useMemo, useEffect } = React;

// ─── Tiny inline icons ──────────────────────────────────────────
const Icon = {
  Check: (p) => (<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M3 8.5l3.5 3.5L13 4.5"/></svg>),
  X: (p) => (<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M4 4l8 8M12 4l-8 8"/></svg>),
  Info: (p) => (<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.6" {...p}><circle cx="8" cy="8" r="6.5"/><path d="M8 7v4M8 5v.01" strokeLinecap="round"/></svg>),
  Shield: (p) => (<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" {...p}><path d="M8 1.5L2.5 4v4.5c0 3.2 2.4 5.6 5.5 6.5 3.1-.9 5.5-3.3 5.5-6.5V4L8 1.5z"/><path d="M5.5 8l2 2 3-3" strokeLinecap="round"/></svg>),
  Lock: (p) => (<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.6" {...p}><rect x="3.5" y="7" width="9" height="6.5" rx="1"/><path d="M5.5 7V5a2.5 2.5 0 015 0v2"/></svg>),
  Sparkle: (p) => (<svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor" {...p}><path d="M8 1l1.5 4.5L14 7l-4.5 1.5L8 13 6.5 8.5 2 7l4.5-1.5z"/></svg>),
  Clock: (p) => (<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.6" {...p}><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5V8l2.5 1.5" strokeLinecap="round"/></svg>),
  Bot: () => <span style={{fontSize:'12px'}}>🤖</span>,
  Human: () => <span style={{fontSize:'12px'}}>🧑</span>,
  Python: () => <span style={{fontSize:'12px'}}>🐍</span>,
  Llm: () => <span style={{fontSize:'12px'}}>✨</span>,
};

// ─── Helpers ────────────────────────────────────────────────────
const confColor = (c) => {
  if (c >= 0.85) return '#1f7a4d';
  if (c >= 0.75) return '#1B4F8A';
  if (c >= 0.65) return '#b56a0a';
  return '#c8323a';
};
const confLabel = (c) => {
  if (c >= 0.85) return 'Alta';
  if (c >= 0.75) return 'Aceptable';
  if (c >= 0.65) return 'Por debajo de umbral';
  return 'Baja';
};

// ─── Header ─────────────────────────────────────────────────────
function Header() {
  return (
    <header className="header">
      <div className="brand">
        <img className="brand-logo" src="logo.png" alt="SoberanIA Health" />
        <div className="brand-divider"></div>
        <div className="brand-tag">
          <span className="brand-tag-strong">Authorization Console</span>
          HM Hospitales · Demo Back-office Administrativo
        </div>
      </div>
      <div className="header-status">
        <span className="status-pill">
          <span className="status-dot"></span>
          API conectada
        </span>
        <span className="status-pill warn">
          <span className="status-dot"></span>
          Mock mode activo
        </span>
        <span className="version-pill">calculadores v1.0.0-simulado</span>
        <div className="header-user" title="Dr. M. Aguilar">MA</div>
      </div>
    </header>
  );
}

// ─── Metrics ────────────────────────────────────────────────────
function Metrics({ data, pendientes }) {
  return (
    <div className="metrics">
      <div className="metric">
        <div className="metric-label">Procesadas hoy</div>
        <div className="metric-value">{data.procesadas}<span className="metric-unit">solicitudes</span></div>
        <div className="metric-foot">
          <span className="metric-trend up">▲ 12%</span>
          <span>vs ayer · 220</span>
        </div>
      </div>
      <div className="metric">
        <div className="metric-label">Automatizadas sin intervención</div>
        <div className="metric-value">{data.automatizadas}<span className="metric-unit">%</span></div>
        <div className="bar"><div style={{width: `${data.automatizadas}%`}}></div></div>
        <div className="metric-foot">
          <span>{Math.round(data.procesadas * data.automatizadas / 100)} de {data.procesadas} resueltas por agente</span>
        </div>
      </div>
      <div className="metric">
        <div className="metric-label">
          Pendientes revisión
          <span className="badge urgent">2 urgentes</span>
        </div>
        <div className="metric-value">{pendientes}<span className="metric-unit">en cola</span></div>
        <div className="metric-foot">
          <span>SLA medio espera · <span style={{fontFamily:'var(--font-mono)'}}>4m 18s</span></span>
        </div>
      </div>
      <div className="metric">
        <div className="metric-label">Tiempo medio de proceso</div>
        <div className="metric-value">{data.tiempoMedio}<span className="metric-unit">s</span></div>
        <div className="metric-foot">
          <span className="metric-trend up">▼ 38%</span>
          <span>vs proceso manual · 23 min</span>
        </div>
      </div>
    </div>
  );
}

// ─── Queue ──────────────────────────────────────────────────────
function Queue({ items, selectedId, onSelect, resolved }) {
  const [filter, setFilter] = useState('todos');
  const visible = useMemo(() => items.filter(i => {
    if (resolved.has(i.id)) return false;
    if (filter === 'urgente') return i.urgencia === 'urgente';
    if (filter === 'normal') return i.urgencia === 'normal';
    return true;
  }), [items, filter, resolved]);

  const counts = {
    todos: items.filter(i => !resolved.has(i.id)).length,
    urgente: items.filter(i => i.urgencia === 'urgente' && !resolved.has(i.id)).length,
    normal: items.filter(i => i.urgencia === 'normal' && !resolved.has(i.id)).length,
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">Cola HITL</div>
        <span className="badge neutral">{counts.todos}</span>
        <div className="panel-sub">actualizado hace 4s</div>
      </div>
      <div className="queue-filters">
        {[
          ['todos', 'Todos', counts.todos],
          ['urgente', 'Urgentes', counts.urgente],
          ['normal', 'Normales', counts.normal],
        ].map(([k, l, c]) => (
          <button key={k} className={`queue-filter ${filter === k ? 'active' : ''}`} onClick={() => setFilter(k)}>
            {l}<span className="queue-filter-count">{c}</span>
          </button>
        ))}
      </div>
      <div className="queue-list">
        {visible.length === 0 ? (
          <div className="empty" style={{height:'100%'}}>
            <div>
              <div className="empty-mark"><Icon.Check /></div>
              <div style={{fontSize:'13px', color:'var(--text)', fontWeight:500}}>Cola vacía</div>
              <div style={{fontSize:'12px', marginTop:4}}>Todas las autorizaciones resueltas</div>
            </div>
          </div>
        ) : visible.map(item => (
          <div
            key={item.id}
            className={`queue-item ${selectedId === item.id ? 'selected' : ''}`}
            onClick={() => onSelect(item.id)}
          >
            <div className={`queue-urg ${item.urgencia}`}></div>
            <div className="queue-body">
              <div className="queue-line1">
                <div className="queue-paciente">{item.paciente}</div>
                <span className="queue-id">{item.id}</span>
              </div>
              <div className="queue-proc">{item.procedimiento}</div>
              <div className="queue-meta">
                <span className="queue-aseg">{item.aseguradora}</span>
                <span style={{color:'var(--text-faint)'}}>·</span>
                <span className="queue-conf" style={{color: confColor(item.confidence)}}>
                  <div className="conf-bar"><div style={{width: `${item.confidence*100}%`, background: confColor(item.confidence)}}></div></div>
                  {item.confidence.toFixed(2)}
                </span>
              </div>
            </div>
            <div className="queue-time">{item.recibido}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Detail ─────────────────────────────────────────────────────
function FlowStep({ step }) {
  const tipoMap = {
    llm: { icon: '✨', label: 'LLM', cls: 'llm' },
    python: { icon: '🐍', label: 'Python', cls: 'python' },
    hitl: { icon: '🧑', label: 'HITL', cls: 'hitl' },
  };
  const t = tipoMap[step.tipo];
  const stateGlyph = step.estado === 'ok'
    ? <span style={{color:'var(--ok)'}}><Icon.Check /></span>
    : step.estado === 'warn'
      ? <span style={{color:'var(--warn)', fontFamily:'var(--font-mono)', fontWeight:700, fontSize:'11px'}}>!</span>
      : <span style={{color:'var(--warn)', fontFamily:'var(--font-mono)', fontSize:'11px'}}>⏳</span>;

  return (
    <div className={`flow-step ${step.estado}`}>
      <div className={`flow-icon ${t.cls}`}>{t.icon}</div>
      <div className="flow-content">
        <div className="flow-name">
          <span className="flow-paso">{step.paso}</span>
          <span className="flow-tipo">{t.label}</span>
          {stateGlyph}
        </div>
        <div className="flow-salida">{step.salida}</div>
      </div>
      <div className="flow-dur">{step.duracion != null ? `${step.duracion}s` : '—'}</div>
    </div>
  );
}

function AuditRow({ row }) {
  const isAgent = row.actor === 'agent';
  return (
    <tr>
      <td className="audit-ts">{row.ts}</td>
      <td>
        <span className="audit-actor">
          <span className={`audit-actor-icon ${isAgent ? 'agent' : 'human'}`}>{isAgent ? '🤖' : '🧑'}</span>
          <span className="audit-actor-name">{row.actorName}</span>
        </span>
      </td>
      <td style={{fontSize:'12px'}}>{row.accion}</td>
      <td className="audit-conf" style={{color: row.confidence != null ? confColor(row.confidence) : 'var(--text-faint)'}}>
        {row.confidence != null ? row.confidence.toFixed(2) : '—'}
      </td>
      <td className="audit-hash">{row.hash}…</td>
    </tr>
  );
}

function Detail({ item, onAction }) {
  const [notes, setNotes] = useState('');
  useEffect(() => { setNotes(''); }, [item?.id]);

  if (!item) {
    return (
      <div className="panel detail">
        <div className="empty">
          <div>
            <div className="empty-mark"><Icon.Info /></div>
            <div style={{fontSize:'14px', color:'var(--text)', fontWeight:500, marginBottom:4}}>
              Selecciona un caso de la cola
            </div>
            <div style={{fontSize:'12px'}}>El detalle, flujo del agente y log de auditoría aparecerán aquí.</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="panel detail">
      <div className="detail-header">
        <div className="detail-header-main">
          <div className="detail-id">
            <span>{item.id}</span>
            <span style={{color:'var(--border-strong)'}}>•</span>
            <span>Recibido a las {item.recibido}</span>
            <span style={{color:'var(--border-strong)'}}>•</span>
            <span>CIE-10 {item.cie}</span>
          </div>
          <div className="detail-title">{item.procedimiento}</div>
          <div className="detail-sub">
            {item.paciente} · {item.edad} años · {item.aseguradora}
          </div>
        </div>
        <span className={`badge ${item.urgencia === 'urgente' ? 'urgent' : 'neutral'}`}>
          {item.urgencia === 'urgente' ? '● Urgente' : '○ Normal'}
        </span>
      </div>

      <div className="detail-body">
        {/* Patient + confidence */}
        <div className="detail-section">
          <div className="section-label">Datos del paciente</div>
          <div className="patient-grid">
            <div>
              <div className="field-label">Nombre</div>
              <div className="field-value">{item.paciente}</div>
            </div>
            <div>
              <div className="field-label">Aseguradora</div>
              <div className="field-value">{item.aseguradora}</div>
            </div>
            <div>
              <div className="field-label">Nº póliza</div>
              <div className="field-value mono">{item.poliza}</div>
            </div>
            <div>
              <div className="field-label">Procedimiento</div>
              <div className="field-value">{item.procedimiento} <span style={{color:'var(--text-faint)', fontFamily:'var(--font-mono)', fontSize:'12px', fontWeight:400}}>· {item.cie}</span></div>
            </div>
          </div>

          <div className="confidence-block">
            <div className="confidence-row">
              <div>
                <div className="field-label" style={{marginBottom:0}}>Confidence score del agente</div>
                <div className="confidence-tag">{confLabel(item.confidence)} · umbral mínimo 0.75</div>
              </div>
              <div className="confidence-num" style={{color: confColor(item.confidence)}}>
                {item.confidence.toFixed(2)}
              </div>
            </div>
            <div className="confidence-bar">
              <div style={{width: `${item.confidence*100}%`, background: confColor(item.confidence)}}></div>
              <div className="threshold" style={{left: '75%'}}></div>
            </div>
            <div className="confidence-thresholds">
              <span>0.00</span>
              <span style={{marginLeft:'auto', marginRight:'25%'}}>0.75 umbral</span>
              <span>1.00</span>
            </div>
          </div>
        </div>

        {/* Flow */}
        <div className="detail-section">
          <div className="section-label">
            Decisión del agente
            <span style={{color:'var(--text-faint)', textTransform:'none', letterSpacing:0, fontWeight:400, marginLeft:'auto', fontFamily:'var(--font-mono)', fontSize:'10px'}}>
              {item.flujo.length} pasos · {item.flujo.reduce((a,s) => a + (s.duracion||0), 0).toFixed(1)}s
            </span>
          </div>
          <div className="flow">
            {item.flujo.map((s, i) => <FlowStep key={i} step={s} />)}
          </div>
          <div className="hitl-reason">
            <strong>Motivo HITL:</strong> {item.motivoHITL}
          </div>
        </div>

        {/* Audit log */}
        <div className="detail-section">
          <div className="section-label">
            Audit log
            <span style={{marginLeft:'auto', textTransform:'none', letterSpacing:0, fontWeight:400, color:'var(--text-faint)', fontSize:'11px'}}>
              {item.audit.length} eventos
            </span>
          </div>
          <table className="audit-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Acción</th>
                <th>Conf.</th>
                <th>SHA-256</th>
              </tr>
            </thead>
            <tbody>
              {item.audit.map((row, i) => <AuditRow key={i} row={row} />)}
            </tbody>
          </table>
          <div className="integrity-banner">
            <Icon.Shield />
            <span><Icon.Check style={{marginRight:4, verticalAlign:'middle'}} /> SHA-256 íntegro</span>
            <span style={{marginLeft:'auto'}} className="mono">cadena verificada · {item.audit.length}/{item.audit.length} bloques</span>
          </div>
        </div>

        {/* Actions */}
        <div className="detail-section">
          <div className="section-label">Acciones del revisor</div>
          <div className="actions">
            <button className="btn btn-approve" onClick={() => onAction(item.id, 'approve', notes)}>
              <Icon.Check /> Aprobar autorización
            </button>
            <button className="btn btn-reject" onClick={() => onAction(item.id, 'reject', notes)}>
              <Icon.X /> Rechazar
            </button>
            <button className="btn btn-info" onClick={() => onAction(item.id, 'info', notes)}>
              <Icon.Info /> Pedir más información
            </button>
          </div>
          <textarea
            className="notes-field"
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Notas del revisor (opcional) — quedarán registradas en el audit log con tu firma y timestamp."
          />
          <div className="notes-meta">
            <span>Firmado por <strong style={{color:'var(--text-muted)'}}>Dr. M. Aguilar</strong> · Servicio Cardiología HM</span>
            <span style={{fontFamily:'var(--font-mono)'}}>{notes.length} car.</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Footer ─────────────────────────────────────────────────────
function Footer() {
  return (
    <footer className="footer">
      <div className="footer-left">
        <span className="sim-tag">DATA_STATUS: SIMULADO</span>
        <span>Datos simulados — Validación con HM en Fase 0</span>
      </div>
      <div className="footer-right">
        <span className="compliant-tag" style={{color:'var(--ok)'}}>
          <Icon.Shield /> AI Act compliant
        </span>
        <span style={{color:'var(--border-strong)'}}>·</span>
        <span className="compliant-tag">
          <Icon.Lock /> Datos 100% Hetzner EU
        </span>
        <span style={{color:'var(--border-strong)'}}>·</span>
        <span className="mono" style={{color:'var(--text-faint)'}}>build 2026.05.06-r71</span>
      </div>
    </footer>
  );
}

// ─── Toasts ─────────────────────────────────────────────────────
function Toasts({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.kind}`}>
          <span className="toast-icon">{t.kind === 'approved' ? '✅' : t.kind === 'rejected' ? '❌' : '📋'}</span>
          <div className="toast-text">
            <div>{t.text}</div>
            <div className="toast-meta">{t.meta}</div>
          </div>
        </div>
      ))}
    </div>
  );
}


// ─── App (modificado: conecta a la API real) ────────────────────
//
// MISMO COMPORTAMIENTO VISUAL que el App original. Sólo cambian:
//   1. Fuente de datos: window.SOBERANIA_DATA → fetch a /api/v1/*
//   2. handleAction:    toast local → POST + toast
//   3. Auto-refresh cada 15s
//
// Componentes Header, Metrics, Queue, Detail, FlowStep, AuditRow,
// Footer, Toasts e Icon NO se tocan.

const _capCase = (s) => {
  if (!s) return s;
  // Siglas (≤3 chars) en mayúsculas: DKV, IMQ, etc.
  if (s.length <= 3) return s.toUpperCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
};

// Transforma una fila Autorizacion del API al shape que esperan los
// componentes Queue/Detail (sin alterar ningún campo visual).
const transformItem = (a) => {
  const created = a.created_at ? new Date(a.created_at) : new Date();
  return {
    id: a.id.slice(0, 8).toUpperCase(),
    _uuid: a.id,
    urgencia: a.urgencia || 'normal',
    paciente: a.paciente_nombre || '(paciente sin extraer)',
    edad: '—',
    procedimiento: a.procedimiento_descripcion || '(procedimiento sin extraer)',
    cie: a.procedimiento_cie10 || '—',
    aseguradora: _capCase(a.aseguradora || '—'),
    poliza: a.poliza_numero || '—',
    confidence: parseFloat(a.confidence_score || 0),
    recibido: created.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
    motivoHITL: 'Confidence por debajo del umbral 0.80 o catálogo simulado pendiente de validar con HM en Fase 0',
    flujo: [],
    audit: [],
  };
};

const _tipoFromAuditEntry = (e) => {
  if (e.hitl_intervencion) return 'hitl';
  const m = e.modelo_usado || '';
  if (m === 'mock' || m.includes('mistral') || m.includes('nemo')) return 'llm';
  return 'python';
};

// Enriquece un item con datos del audit log (flujo + tabla audit).
const enrichItem = (item, audit) => {
  if (!audit || !audit.entries) return item;
  const flujo = audit.entries.map(e => ({
    paso: e.accion,
    tipo: _tipoFromAuditEntry(e),
    estado: 'ok',
    duracion: 0.4,
    salida: e.resultado || '—',
  }));
  const auditRows = audit.entries.map(e => ({
    ts: (e.timestamp || '').replace('T', ' ').slice(0, 19),
    accion: e.accion,
    actor: e.hitl_intervencion ? 'human' : 'agent',
    actorName: e.actor,
    confidence: e.confidence_score != null ? parseFloat(e.confidence_score) : null,
    hash: (e.hash_sha256 || '').slice(0, 12),
  }));
  return { ...item, flujo, audit: auditRows };
};

// ─── Pestaña Auditoría AI Act ───────────────────────────────────
//
// Vista secundaria (no visible para back-office, solo accesible desde
// el selector ViewTabs). Lista TODAS las autorizaciones — no solo las
// pendientes — y para cada una muestra el reporte AI Act completo
// devuelto por GET /api/v1/audit/{id}/aiact-report.
// Reglas:
//   - 🤖 LLM · 🐍 Python puro · 🧑 Humano (icono por tipo de actor)
//   - SHA256 banner verde si íntegro, rojo si comprometido
//   - Botón "Exportar JSON" descarga el reporte completo
//   - Métricas compliance: % supervisión, % contradicciones, tiempo medio

function ViewTabs({ vista, onChange }) {
  const tabs = [
    { id: 'hitl', label: 'Cola HITL' },
    { id: 'auditoria', label: 'Auditoría AI Act' },
  ];
  return (
    <div style={{
      display: 'flex',
      gap: 0,
      padding: '0 24px',
      background: 'var(--bg, #fff)',
      borderBottom: '1px solid var(--border, #e4e8ee)',
    }}>
      {tabs.map(t => {
        const active = vista === t.id;
        return (
          <button
            key={t.id}
            onClick={() => onChange(t.id)}
            style={{
              padding: '12px 18px',
              background: 'transparent',
              border: 'none',
              borderBottom: active ? '2px solid #1B4F8A' : '2px solid transparent',
              color: active ? '#1B4F8A' : '#6b7280',
              fontWeight: active ? 600 : 500,
              fontSize: 13,
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}

function ReporteAIAct({ report, onExport }) {
  const a = report.autorizacion;
  const tipoIcon = { llm: '🤖', python: '🐍', hitl: '🧑' };
  return (
    <div>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:16,gap:12}}>
        <div>
          <div style={{fontSize:11,color:'#6b7280',textTransform:'uppercase',letterSpacing:0.5,fontWeight:600}}>Reporte AI Act</div>
          <div style={{fontSize:14,fontWeight:600,marginTop:4}}>{a.paciente_nombre || '(sin nombre)'}</div>
          <div style={{fontSize:11,color:'#9ca3af',fontFamily:'ui-monospace,monospace',marginTop:2}}>{a.id}</div>
        </div>
        <button onClick={onExport} style={{
          padding:'8px 14px',background:'#1B4F8A',color:'#fff',
          border:'none',borderRadius:6,cursor:'pointer',fontSize:12,fontWeight:500,
          whiteSpace:'nowrap',
        }}>↓ Exportar JSON</button>
      </div>

      <section style={{marginBottom:18}}>
        <div style={{textTransform:'uppercase',fontSize:10,color:'#6b7280',marginBottom:8,fontWeight:600,letterSpacing:0.5}}>Datos del paciente y orden</div>
        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:6,fontSize:12}}>
          <div><span style={{color:'#6b7280'}}>Paciente:</span> {a.paciente_nombre || '—'}</div>
          <div><span style={{color:'#6b7280'}}>Aseguradora:</span> {a.aseguradora || '—'}</div>
          <div><span style={{color:'#6b7280'}}>Médico:</span> {a.medico_nombre || '—'}</div>
          <div><span style={{color:'#6b7280'}}>Procedimiento:</span> {a.procedimiento_descripcion || '—'}</div>
          <div><span style={{color:'#6b7280'}}>CIE-10:</span> {a.procedimiento_cie10 || '—'}</div>
          <div><span style={{color:'#6b7280'}}>Código aseguradora:</span> {a.procedimiento_codigo || '—'}</div>
          <div><span style={{color:'#6b7280'}}>Estado final:</span> <strong>{a.estado_final}</strong></div>
          <div><span style={{color:'#6b7280'}}>Tiempo total:</span> {a.tiempo_total_segundos != null ? `${a.tiempo_total_segundos}s` : '—'}</div>
        </div>
      </section>

      <section style={{marginBottom:18}}>
        <div style={{textTransform:'uppercase',fontSize:10,color:'#6b7280',marginBottom:8,fontWeight:600,letterSpacing:0.5}}>
          Pasos del agente · {report.audit.total_pasos}
        </div>
        {report.audit.pasos.map((p, i) => (
          <div key={i} style={{
            padding:'10px 12px',
            borderLeft: '3px solid ' + (p.tipo === 'hitl' ? '#b56a0a' : p.tipo === 'llm' ? '#1B4F8A' : '#1f7a4d'),
            marginBottom:6,
            background:'#f9fafb',
            borderRadius:'0 4px 4px 0',
            fontSize:12,
          }}>
            <div style={{display:'flex',gap:8,alignItems:'center',marginBottom:4,flexWrap:'wrap'}}>
              <span style={{fontSize:14}}>{tipoIcon[p.tipo] || '?'}</span>
              <strong>{p.accion}</strong>
              <span style={{color:'#6b7280',fontSize:11}}>{p.actor}</span>
              <span style={{marginLeft:'auto',fontFamily:'ui-monospace,monospace',color:'#6b7280',fontSize:11}}>
                {p.timestamp ? p.timestamp.slice(11, 19) : '—'}
              </span>
            </div>
            <div style={{color:'#374151',fontSize:11,marginBottom:6,lineHeight:1.5}}>
              {p.razon_decision || '—'}
            </div>
            <div style={{display:'flex',gap:12,fontSize:10,color:'#9ca3af',fontFamily:'ui-monospace,monospace',flexWrap:'wrap'}}>
              <span>modelo: {p.modelo_version || '—'}</span>
              <span>modo: {p.modo_inferencia || '—'}</span>
              {p.confidence_score != null && <span>conf: {p.confidence_score.toFixed(2)}</span>}
              <span>sha256: {(p.hash_sha256 || '').slice(0, 16)}…</span>
            </div>
          </div>
        ))}
      </section>

      {report.intervencion_humana && (
        <section style={{marginBottom:18,padding:12,background:'#fef9e7',borderRadius:6,border:'1px solid #f3d869'}}>
          <div style={{textTransform:'uppercase',fontSize:10,color:'#6b7280',marginBottom:8,fontWeight:600,letterSpacing:0.5}}>
            Intervención humana 🧑
          </div>
          <div style={{fontSize:12,display:'grid',gap:4}}>
            <div><span style={{color:'#6b7280'}}>Revisor:</span> <strong>{report.intervencion_humana.revisor}</strong></div>
            <div><span style={{color:'#6b7280'}}>Decisión:</span> <strong>{report.intervencion_humana.decision}</strong></div>
            <div><span style={{color:'#6b7280'}}>Tiempo en cola:</span> {report.intervencion_humana.tiempo_en_cola_segundos}s</div>
            <div>
              <span style={{color:'#6b7280'}}>Coincide con agente:</span>{' '}
              {report.intervencion_humana.coincide_con_agente
                ? <span style={{color:'#1f7a4d',fontWeight:600}}>✓ Sí</span>
                : <span style={{color:'#c8323a',fontWeight:600}}>✗ NO — humano contradijo</span>}
            </div>
            {report.intervencion_humana.notas && (
              <div><span style={{color:'#6b7280'}}>Notas:</span> {report.intervencion_humana.notas}</div>
            )}
          </div>
        </section>
      )}

      <section style={{padding:12,background: report.audit.integro ? '#ecfdf5' : '#fef2f2',borderRadius:6,fontSize:12,border: '1px solid '+(report.audit.integro ? '#a7f3d0' : '#fecaca')}}>
        <div style={{display:'flex',gap:12,alignItems:'center'}}>
          <span style={{fontSize:18}}>{report.audit.integro ? '🔒' : '⚠️'}</span>
          <div>
            <strong style={{color: report.audit.integro ? '#1f7a4d' : '#c8323a'}}>
              {report.audit.integro ? 'AI Act compliant — cadena SHA-256 íntegra' : 'INTEGRIDAD COMPROMETIDA'}
            </strong>
            <div style={{color:'#6b7280',marginTop:2,fontSize:11}}>
              Calculadores: {report.compliance.calculadores_version} · DATA_STATUS: {report.compliance.data_status}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function AuditoriaView() {
  const [todas, setTodas] = useState([]);
  const [metricas, setMetricas] = useState(null);
  const [reportSel, setReportSel] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  const refresh = async () => {
    try {
      const [a, m] = await Promise.all([
        fetch('/api/v1/autorizaciones/').then(r => r.json()),
        fetch('/api/v1/autorizaciones/metricas-aiact').then(r => r.json()),
      ]);
      setTodas(a);
      setMetricas(m);
    } catch (e) {
      console.warn('audit refresh failed:', e);
    }
  };

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 15000);
    return () => clearInterval(t);
  }, []);

  const cargarReporte = async (id) => {
    setSelectedId(id);
    try {
      const r = await fetch(`/api/v1/audit/${id}/aiact-report`).then(r => r.json());
      setReportSel(r);
    } catch (e) {
      console.warn('report fetch failed:', e);
    }
  };

  const exportarJSON = () => {
    if (!reportSel) return;
    const blob = new Blob([JSON.stringify(reportSel, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `aiact-report-${reportSel.autorizacion.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{padding:24,display:'flex',flexDirection:'column',gap:16}}>
      <div style={{
        display:'grid',gridTemplateColumns:'repeat(3, 1fr)',gap:12,
        padding:16,background:'#fff',border:'1px solid #e4e8ee',borderRadius:8,
      }}>
        {!metricas ? <div style={{gridColumn:'span 3',color:'#6b7280'}}>Cargando métricas…</div> : (
          <>
            <div>
              <div style={{fontSize:10,color:'#6b7280',textTransform:'uppercase',letterSpacing:0.5,fontWeight:600}}>% supervisión humana</div>
              <div style={{fontSize:28,fontWeight:700,marginTop:4}}>{Math.round((metricas.porcentaje_supervision || 0) * 100)}%</div>
              <div style={{fontSize:11,color:'#6b7280',marginTop:2}}>{metricas.con_supervision_humana} de {metricas.total_autorizaciones} autorizaciones</div>
            </div>
            <div>
              <div style={{fontSize:10,color:'#6b7280',textTransform:'uppercase',letterSpacing:0.5,fontWeight:600}}>% humano contradijo agente</div>
              <div style={{fontSize:28,fontWeight:700,marginTop:4}}>{Math.round((metricas.porcentaje_contradicciones || 0) * 100)}%</div>
              <div style={{fontSize:11,color:'#6b7280',marginTop:2}}>{metricas.humano_contradijo_agente} de {metricas.decisiones_humanas_registradas} decisiones</div>
            </div>
            <div>
              <div style={{fontSize:10,color:'#6b7280',textTransform:'uppercase',letterSpacing:0.5,fontWeight:600}}>Tiempo medio revisión</div>
              <div style={{fontSize:28,fontWeight:700,marginTop:4}}>
                {metricas.tiempo_medio_revision_segundos != null
                  ? `${metricas.tiempo_medio_revision_segundos.toFixed(1)}s`
                  : '—'}
              </div>
              <div style={{fontSize:11,color:'#6b7280',marginTop:2}}>tiempo en cola HITL</div>
            </div>
          </>
        )}
      </div>

      <div style={{display:'grid',gridTemplateColumns:'380px 1fr',gap:16,minHeight:500}}>
        <div style={{background:'#fff',border:'1px solid #e4e8ee',borderRadius:8,overflow:'hidden',display:'flex',flexDirection:'column'}}>
          <div style={{padding:'12px 16px',borderBottom:'1px solid #e4e8ee',display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <strong style={{fontSize:13}}>Todas las autorizaciones</strong>
            <span style={{color:'#6b7280',fontSize:12}}>{todas.length}</span>
          </div>
          <div style={{flex:1,overflowY:'auto',maxHeight:600}}>
            {todas.length === 0 ? (
              <div style={{padding:20,textAlign:'center',color:'#9ca3af',fontSize:12}}>
                Sin autorizaciones todavía
              </div>
            ) : todas.map(a => {
              const sel = selectedId === a.id;
              const estadoColor = {
                autorizado: '#1f7a4d',
                aprobado_hitl: '#1f7a4d',
                rechazado_hitl: '#c8323a',
                denegado: '#c8323a',
                pendiente_hitl: '#b56a0a',
                informacion_adicional_requerida: '#b56a0a',
              }[a.estado] || '#6b7280';
              return (
                <div key={a.id}
                  onClick={() => cargarReporte(a.id)}
                  style={{
                    padding:'10px 16px',
                    borderBottom:'1px solid #f3f4f6',
                    cursor:'pointer',
                    background: sel ? '#eef2ff' : 'transparent',
                  }}>
                  <div style={{fontSize:13,fontWeight:500}}>{a.paciente_nombre || '(sin nombre)'}</div>
                  <div style={{fontSize:11,color:'#6b7280',marginTop:2,display:'flex',gap:6,flexWrap:'wrap'}}>
                    <span>{(a.aseguradora || '—').toUpperCase()}</span>
                    <span>·</span>
                    <span style={{color: estadoColor, fontWeight:500}}>{a.estado}</span>
                    {a.hitl_revisor && <><span>·</span><span style={{color:'#b56a0a'}}>🧑 {a.hitl_revisor}</span></>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div style={{background:'#fff',border:'1px solid #e4e8ee',borderRadius:8,padding:20,overflowY:'auto',maxHeight:800}}>
          {!reportSel ? (
            <div style={{color:'#9ca3af',textAlign:'center',padding:60,fontSize:13}}>
              Selecciona una autorización para ver su reporte AI Act completo
            </div>
          ) : (
            <ReporteAIAct report={reportSel} onExport={exportarJSON} />
          )}
        </div>
      </div>
    </div>
  );
}

function App() {
  const [vista, setVista] = useState('hitl');  // 'hitl' | 'auditoria'
  const [data, setData] = useState({ procesadas: 0, automatizadas: 0, tiempoMedio: 14.3 });
  const [items, setItems] = useState([]);
  const [resolved, setResolved] = useState(new Set());
  const [selectedId, setSelectedId] = useState(null);
  const [toasts, setToasts] = useState([]);
  const [auditCache, setAuditCache] = useState({});

  const refresh = async () => {
    try {
      const [metricasResp, pendientesResp] = await Promise.all([
        fetch('/api/v1/autorizaciones/metricas'),
        fetch('/api/v1/autorizaciones/pendientes'),
      ]);
      const metricas = await metricasResp.json();
      const pendientes = await pendientesResp.json();
      setData({
        procesadas: metricas.total || 0,
        automatizadas: Math.round((metricas.tasa_automatizacion || 0) * 100),
        tiempoMedio: 14.3,
      });
      setItems(pendientes.map(transformItem));
    } catch (e) {
      console.warn('refresh failed:', e);
    }
  };

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 15000);
    return () => clearInterval(t);
  }, []);

  // Audit fetch al seleccionar caso
  useEffect(() => {
    if (!selectedId) return;
    const item = items.find(i => i.id === selectedId);
    if (!item || auditCache[item._uuid]) return;
    fetch(`/api/v1/audit/${item._uuid}`)
      .then(r => r.json())
      .then(audit => setAuditCache(prev => ({ ...prev, [item._uuid]: audit })))
      .catch(e => console.warn('audit fetch failed:', e));
  }, [selectedId, items]);

  const visible = items.filter(i => !resolved.has(i.id));
  const selected = items.find(i => i.id === selectedId && !resolved.has(i.id));

  // Auto-select first available if current is gone
  useEffect(() => {
    if (!selected && visible.length > 0) setSelectedId(visible[0].id);
  }, [selected, visible]);

  const enriched = selected ? enrichItem(selected, auditCache[selected._uuid]) : null;

  const pushToast = (t) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { ...t, id }]);
    setTimeout(() => setToasts(prev => prev.filter(x => x.id !== id)), 3500);
  };

  const handleAction = async (id, kind, notes) => {
    const item = items.find(i => i.id === id);
    if (!item) return;
    const decisionMap = { approve: 'aprobar', reject: 'rechazar', info: 'mas_info' };
    try {
      const resp = await fetch(`/api/v1/autorizaciones/${item._uuid}/hitl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: decisionMap[kind],
          notas: notes || '',
          revisor: 'demo@hm.es',
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      const labels = {
        approve: { kind: 'approved', text: `Autorización ${id} aprobada`, meta: `${item.paciente} · ${item.aseguradora} · firmado por Dr. M. Aguilar` },
        reject: { kind: 'rejected', text: `Autorización ${id} rechazada`, meta: notes ? `Motivo registrado · ${notes.length} car.` : 'Sin motivo registrado' },
        info: { kind: 'info', text: `Solicitud de información enviada`, meta: `${item.paciente} · vía portal aseguradora` },
      };
      pushToast(labels[kind]);
      if (kind !== 'info') {
        setResolved(prev => new Set([...prev, id]));
      }
      setTimeout(refresh, 600);
    } catch (e) {
      pushToast({
        kind: 'rejected',
        text: 'Error al guardar decisión',
        meta: String(e.message || e),
      });
    }
  };

  return (
    <div className="app">
      <Header />
      <ViewTabs vista={vista} onChange={setVista} />
      {vista === 'hitl' ? (
        <>
          <Metrics data={data} pendientes={visible.length} />
          <div className="main">
            <Queue items={items} selectedId={selectedId} onSelect={setSelectedId} resolved={resolved} />
            <Detail item={enriched} onAction={handleAction} />
          </div>
        </>
      ) : (
        <AuditoriaView />
      )}
      <Footer />
      <Toasts toasts={toasts} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
