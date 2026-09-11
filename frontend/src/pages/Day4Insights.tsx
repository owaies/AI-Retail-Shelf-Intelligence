import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../services/api'
import type { Analysis, AnalysisSummary } from '../types'

function ErrorNotice({ message }: { message: string }) { return <div className="error-notice" role="alert"><strong>REQUEST ERROR</strong><span>{message}</span></div> }
function EmptyPanel({ title, text }: { title: string; text: string }) { return <div className="empty-panel"><span className="cross" aria-hidden="true">+</span><strong>{title}</strong><p>{text}</p></div> }
function downloadCsv(filename: string, rows: string[][]) {
  const escape = (value: string) => `"${value.replace(/"/g, '""')}"`
  const csv = rows.map(row => row.map(escape).join(',')).join('\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const anchor = document.createElement('a')
  anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url)
}

export function Day4HistoryPage() {
  const [items, setItems] = useState<AnalysisSummary[]>([])
  const [query, setQuery] = useState('')
  const [model, setModel] = useState('ALL')
  const [sort, setSort] = useState<'newest' | 'oldest' | 'detections'>('newest')
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()
  const [selected, setSelected] = useState<Analysis | null>(null)
  const [loadingSelected, setLoadingSelected] = useState(false)
  const selectedId = searchParams.get('id')

  useEffect(() => { api.analyses().then(setItems).catch(e => setError(e.message)) }, [])
  useEffect(() => {
    if (!selectedId) { setSelected(null); return }
    setLoadingSelected(true); setError('')
    api.analysis(selectedId).then(setSelected).catch(e => setError(e.message)).finally(() => setLoadingSelected(false))
  }, [selectedId])
  const models = useMemo(() => [...new Set(items.map(item => item.model_name))].sort(), [items])
  const filtered = useMemo(() => items.filter(item => item.image_name.toLowerCase().includes(query.trim().toLowerCase()) && (model === 'ALL' || item.model_name === model)).sort((a, b) => sort === 'detections' ? b.detection_count - a.detection_count : sort === 'newest' ? +new Date(b.created_at) - +new Date(a.created_at) : +new Date(a.created_at) - +new Date(b.created_at)), [items, model, query, sort])
  const exportHistory = () => downloadCsv('retail-vision-history.csv', [['Image', 'Detections', 'Model', 'Version', 'Status', 'Created At'], ...filtered.map(item => [item.image_name, String(item.detection_count), item.model_name, item.model_version, item.status, item.created_at])])
  const remove = async (id: string) => {
    if (!window.confirm('Delete this analysis record? This cannot be undone.')) return
    setDeleting(true); setError('')
    try { await api.deleteAnalysis(id); setItems(current => current.filter(item => item.id !== id)); if (selectedId === id) setSearchParams({}) }
    catch (e) { setError(e instanceof Error ? e.message : 'Delete failed') }
    finally { setDeleting(false) }
  }
  return <>
    <section className="page-header"><div className="eyebrow"><span>03</span>ANALYSIS HISTORY / DAY 4</div><h1>Find the signal.</h1><p>Search, filter, sort, inspect, export, and safely manage real authenticated analysis records.</p></section>
    {error && <ErrorNotice message={error} />}
    {selectedId && <section className="panel day4-detail" aria-label="Analysis details">
      <div className="detail-top"><div><div className="panel-label">ANALYSIS / DETAIL</div><h2>{loadingSelected ? 'Loading record…' : selected?.image_name || 'Record unavailable'}</h2></div><button className="secondary-button" type="button" onClick={() => setSearchParams({})}>CLOSE</button></div>
      {selected && <div className="detail-grid"><div><span>STATUS</span><strong>{selected.status}</strong></div><div><span>DETECTIONS</span><strong>{selected.detection_count}</strong></div><div><span>MODEL</span><strong>{selected.model_name} {selected.model_version}</strong></div><div><span>IMAGE</span><strong>{selected.image_width} × {selected.image_height}</strong></div><div><span>CREATED</span><strong>{new Date(selected.created_at).toLocaleString()}</strong></div><div><span>COMPLETED</span><strong>{selected.completed_at ? new Date(selected.completed_at).toLocaleString() : '—'}</strong></div></div>}
      {selected && <div className="detail-detections"><div className="panel-label">DETECTION RECORDS</div>{selected.detections.length ? selected.detections.map((detection, index) => <div className="detection-row" key={`${detection.class_name}-${index}`}><strong>{detection.class_name}</strong><span>{(detection.confidence * 100).toFixed(1)}% confidence</span><small>x {Math.round(detection.box.x)} · y {Math.round(detection.box.y)} · w {Math.round(detection.box.width)} · h {Math.round(detection.box.height)}</small></div>) : <p className="muted-copy">No detections were persisted for this analysis.</p>}</div>}
      {selected && <div className="detail-note"><span className="panel-label">SHELF ASSESSMENT</span><strong>{selected.shelf_assessment.status}</strong><p>{selected.shelf_assessment.note}</p></div>}
    </section>}
    <section className="history-toolbar panel" aria-label="History filters">
      <label><span>SEARCH IMAGE</span><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search filename" /></label>
      <label><span>MODEL</span><select value={model} onChange={e => setModel(e.target.value)}><option value="ALL">ALL MODELS</option>{models.map(name => <option key={name} value={name}>{name}</option>)}</select></label>
      <label><span>SORT</span><select value={sort} onChange={e => setSort(e.target.value as typeof sort)}><option value="newest">NEWEST</option><option value="oldest">OLDEST</option><option value="detections">MOST DETECTIONS</option></select></label>
      <div className="filter-count"><strong>{filtered.length}</strong><span>VISIBLE / {items.length} TOTAL</span></div>
      <button className="secondary-button export-button" type="button" onClick={exportHistory} disabled={!filtered.length}>EXPORT CSV</button>
    </section>
    {deleting && <div className="notice"><strong>UPDATING HISTORY</strong><p>Deleting the selected record…</p></div>}
    {filtered.length ? <div className="data-table day4-table" role="table"><div className="data-row data-head"><span>IMAGE</span><span>DETECTIONS</span><span>MODEL</span><span>DATE</span><span>ACTION</span></div>{filtered.map(item => <div className="data-row" role="row" key={item.id}><Link className="data-cell-link" to={`/history?id=${item.id}`}><strong>{item.image_name}</strong><small>{item.status}</small></Link><span>{item.detection_count}</span><span>{item.model_name}<small>{item.model_version}</small></span><span>{new Date(item.created_at).toLocaleString()}</span><button className="delete-button" type="button" onClick={() => remove(item.id)}>DELETE</button></div>)}</div> : <EmptyPanel title="NO MATCHING ANALYSES" text={items.length ? 'Try another filename, model, or sort order.' : 'Completed analyses will appear here after a successful authenticated run.'} />}
  </>
}

export function Day4AnalyticsPage() {
  const [items, setItems] = useState<AnalysisSummary[]>([])
  const [details, setDetails] = useState<Analysis[]>([])
  const [error, setError] = useState('')
  const [loadingDetails, setLoadingDetails] = useState(false)
  useEffect(() => { api.analyses().then(setItems).catch(e => setError(e.message)) }, [])
  useEffect(() => {
    if (!items.length) { setDetails([]); return }
    setLoadingDetails(true)
    Promise.all(items.map(item => api.analysis(item.id))).then(setDetails).catch(e => setError(e.message)).finally(() => setLoadingDetails(false))
  }, [items])
  const total = items.reduce((sum, item) => sum + item.detection_count, 0)
  const average = items.length ? (total / items.length).toFixed(1) : '0'
  const classes = useMemo(() => { const counts: Record<string, number> = {}; details.forEach(item => Object.entries(item.class_counts).forEach(([name, count]) => { counts[name] = (counts[name] || 0) + count })); return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8) }, [details])
  const max = classes[0]?.[1] || 1
  const models = useMemo(() => [...new Set(items.map(item => `${item.model_name} ${item.model_version}`))], [items])
  const exportAnalytics = () => downloadCsv('retail-vision-analytics.csv', [['Class', 'Detections'], ...classes.map(([name, count]) => [name, String(count)])])
  return <>
    <section className="page-header"><div className="eyebrow"><span>04</span>RETAIL TELEMETRY / DAY 4</div><h1>Read the pattern.</h1><p>Derived analytics use only persisted detection records. Stock-level claims are intentionally excluded.</p></section>
    {error && <ErrorNotice message={error} />}
    <section className="analytics-grid day4-analytics-grid"><article className="panel"><div className="panel-label">ANALYSES</div><div className="big-zero">{items.length}</div><p>Total stored analysis records.</p></article><article className="panel"><div className="panel-label">DETECTIONS</div><div className="big-zero">{total}</div><p>Total detections across the dataset.</p></article><article className="panel"><div className="panel-label">AVERAGE / SCAN</div><div className="big-zero">{average}</div><p>Mean detections per stored analysis.</p></article><article className="panel"><div className="panel-label">MODEL / VERSIONS</div><div className="analytics-list">{models.length ? models.map(model => <span key={model}>{model}</span>) : <span>NO DATA</span>}</div><p>Versions represented in persisted records.</p></article></section>
    <section className="section-block"><div className="section-heading"><div><span className="panel-label">CLASS / DISTRIBUTION</span><h2>Detection mix</h2></div><div className="section-actions"><span className="mono">{loadingDetails ? 'LOADING DETAILS…' : `TOP ${classes.length} CLASSES`}</span><button className="secondary-button" type="button" onClick={exportAnalytics} disabled={!classes.length}>EXPORT CSV</button></div></div><article className="panel class-chart">{classes.length ? classes.map(([name, count]) => <div className="bar-row" key={name}><div><strong>{name}</strong><span>{count}</span></div><div className="bar-track"><span style={{ width: `${count / max * 100}%` }} /></div></div>) : <EmptyPanel title={loadingDetails ? 'LOADING DETECTION DATA' : 'NO DETECTION DATA'} text={loadingDetails ? 'Loading persisted analysis details…' : 'Run an analysis to populate class distribution telemetry.'} />}</article></section>
    <section className="panel evidence-card"><div className="panel-label">EVIDENCE / BOUNDARY</div><strong>STOCK STATUS NOT CLAIMED</strong><p>The detector output is summarized as observations only. It does not estimate inventory, availability, facings, or out-of-stock state.</p></section>
  </>
}
