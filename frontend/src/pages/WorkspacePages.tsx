import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, getAccessToken, setAccessToken } from '../services/api'
import type { Analysis, AnalysisSummary } from '../types'

function PageHeader({ index, eyebrow, title, description }: { index: string; eyebrow: string; title: string; description: string }) {
  return <section className="page-header"><div className="eyebrow"><span>{index}</span>{eyebrow}</div><h1>{title}</h1><p>{description}</p></section>
}
function EmptyPanel({ title, text, action }: { title: string; text: string; action?: React.ReactNode }) {
  return <div className="empty-panel"><span className="cross" aria-hidden="true">+</span><strong>{title}</strong><p>{text}</p>{action}</div>
}
function ErrorNotice({ message }: { message: string }) { return <div className="error-notice" role="alert"><strong>REQUEST ERROR</strong><span>{message}</span></div> }

export function DashboardPage() {
  const [items, setItems] = useState<AnalysisSummary[]>([])
  const [health, setHealth] = useState('CHECKING')
  const [error, setError] = useState('')
  useEffect(() => { api.analyses().then(setItems).catch(e => setError(e.message)); api.health().then(() => setHealth('ONLINE')).catch(() => setHealth('OFFLINE')) }, [])
  const detections = items.reduce((sum, item) => sum + item.detection_count, 0)
  return <>
    <PageHeader index="01" eyebrow="COMMAND CENTER" title="Shelf intelligence." description="Turn shelf imagery into traceable computer-vision observations with real detections and confidence scores." />
    {error && <ErrorNotice message={error} />}
    <section className="hero-grid">
      <article className="panel hero-panel"><div className="panel-label">VISION / CONNECTED</div><h2>See the shelf.<br /><span>Know the shelf.</span></h2><p>Upload a shelf image, run the backend vision pipeline, and inspect every returned detection instead of relying on placeholder analytics.</p><Link className="primary-button" to="/analyze">START ANALYSIS <span>↗</span></Link></article>
      <div className="metric-stack"><article className="metric-card"><span>ANALYSES</span><strong>{items.length}</strong><small>Stored analysis records</small></article><article className="metric-card accent"><span>DETECTIONS</span><strong>{detections}</strong><small>Across loaded analyses</small></article><article className="metric-card"><span>API</span><strong>{health}</strong><small>FastAPI health endpoint</small></article></div>
    </section>
    <section className="section-block"><div className="section-heading"><div><span className="panel-label">RECENT / ANALYSIS LOG</span><h2>Recent analyses</h2></div><Link className="text-link" to="/history">VIEW HISTORY ↗</Link></div>
      {items.length ? <AnalysisTable items={items.slice(0, 5)} /> : <EmptyPanel title="NO ANALYSES RECORDED" text="Create an authenticated analysis to populate this workspace." action={<Link className="secondary-button" to="/settings">CONFIGURE ACCESS</Link>} />}
    </section>
  </>
}

function Pipeline({ active }: { active: number }) {
  return <ol className="pipeline">{['Validate image', 'Preprocess with OpenCV', 'Run YOLO inference', 'Analyze detections', 'Store result'].map((step, index) => <li key={step} className={index < active ? 'done' : index === active ? 'current' : ''}><span>{String(index + 1).padStart(2, '0')}</span><strong>{step}</strong><small>{index < active ? 'DONE' : index === active ? 'RUNNING' : 'WAITING'}</small></li>)}</ol>
}

export function AnalyzePage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState('')
  const [result, setResult] = useState<Analysis | null>(null)
  const [busy, setBusy] = useState(false)
  const [step, setStep] = useState(-1)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])
  const choose = (next: File | undefined) => { if (!next) return; setError(''); setResult(null); setFile(next); setPreview(URL.createObjectURL(next)) }
  const analyze = async () => {
    if (!file) return
    setBusy(true); setError(''); setStep(0)
    try { setStep(1); await new Promise(r => setTimeout(r, 100)); setStep(2); const data = await api.createAnalysis(file); setStep(4); setResult(data) }
    catch (e) { setError(e instanceof Error ? e.message : 'Analysis failed'); setStep(-1) }
    finally { setBusy(false) }
  }
  return <>
    <PageHeader index="02" eyebrow="SHELF ANALYSIS" title="Read the shelf." description="Upload an image and inspect the actual backend response. The UI never invents detections or stock status." />
    {error && <ErrorNotice message={error} />}
    <section className="analysis-workspace">
      <article className="panel upload-panel">
        <div className="panel-label">INPUT / IMAGE</div>
        <input ref={inputRef} className="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp" onChange={e => choose(e.target.files?.[0])} />
        {!file ? <button className="upload-zone" type="button" onClick={() => inputRef.current?.click()} onKeyDown={e => { if (e.key === 'Enter') inputRef.current?.click() }}><div className="scan-icon" aria-hidden="true">⌁</div><h2>Upload shelf image</h2><p>JPEG, PNG or WebP · 10 MB maximum</p><span className="secondary-button">CHOOSE IMAGE</span></button> : <div className="image-stage"><img src={preview} alt={`Selected shelf image: ${file.name}`} /><div className="stage-meta"><span>{file.name}</span><button className="secondary-button" type="button" onClick={() => inputRef.current?.click()}>REPLACE</button></div>{result && <div className="detection-layer" aria-label="Detection overlay">{result.detections.map((d, i) => <div key={`${d.class_name}-${i}`} className="detection-box" style={{ left: `${d.box.x / result.image_width * 100}%`, top: `${d.box.y / result.image_height * 100}%`, width: `${d.box.width / result.image_width * 100}%`, height: `${d.box.height / result.image_height * 100}%` }}><span>{d.class_name} · {(d.confidence * 100).toFixed(0)}%</span></div>)}</div>}</div>}
        <button className="primary-button analyze-button" type="button" disabled={!file || busy} onClick={analyze}>{busy ? 'ANALYZING…' : result ? 'RUN AGAIN' : 'RUN ANALYSIS'} <span>↗</span></button>
      </article>
      <aside className="panel status-panel"><div className="panel-label">PIPELINE / STATUS</div><Pipeline active={step} />{result && <ResultSummary result={result} navigate={navigate} />}{!result && !busy && <div className="notice"><strong>READY</strong><p>Authentication is required by the backend. Configure a valid bearer token in Settings before running a stored analysis.</p></div>}</aside>
    </section>
  </>
}

function ResultSummary({ result, navigate }: { result: Analysis; navigate: ReturnType<typeof useNavigate> }) {
  return <div className="result-card"><div><span className="panel-label">RESULT / COMPLETE</span><strong>{result.detection_count} detections</strong></div><div className="result-grid">{Object.entries(result.class_counts).slice(0, 6).map(([name, count]) => <span key={name}><b>{count}</b>{name}</span>)}</div><p>{result.shelf_assessment.note}</p><button className="secondary-button" type="button" onClick={() => navigate(`/history`)}>OPEN HISTORY</button></div>
}

function AnalysisTable({ items }: { items: AnalysisSummary[] }) {
  return <div className="data-table" role="table"><div className="data-row data-head"><span>IMAGE</span><span>DETECTIONS</span><span>MODEL</span><span>DATE</span></div>{items.map(item => <Link className="data-row" role="row" key={item.id} to={`/history?id=${item.id}`}><span><strong>{item.image_name}</strong><small>{item.status}</small></span><span>{item.detection_count}</span><span>{item.model_name}<small>{item.model_version}</small></span><span>{new Date(item.created_at).toLocaleString()}</span></Link>)}</div>
}

export function HistoryPage() {
  const [items, setItems] = useState<AnalysisSummary[]>([]); const [error, setError] = useState(''); const [selected, setSelected] = useState<Analysis | null>(null)
  useEffect(() => { api.analyses().then(setItems).catch(e => setError(e.message)) }, [])
  useEffect(() => { const id = new URLSearchParams(location.search).get('id'); if (id) api.analysis(id).then(setSelected).catch(e => setError(e.message)) }, [])
  return <><PageHeader index="03" eyebrow="ANALYSIS HISTORY" title="Every scan, traceable." description="Browse real records returned by the FastAPI persistence layer, scoped to the authenticated user." />{error && <ErrorNotice message={error} />}{selected && <section className="panel detail-panel"><div><span className="panel-label">ANALYSIS / {selected.id.slice(0, 8)}</span><h2>{selected.image_name}</h2><p>{selected.detection_count} detections · {selected.model_name} {selected.model_version}</p></div><div className="result-grid">{Object.entries(selected.class_counts).map(([name, count]) => <span key={name}><b>{count}</b>{name}</span>)}</div><p className="muted">{selected.shelf_assessment.note}</p></section>}{items.length ? <AnalysisTable items={items} /> : <EmptyPanel title="NO ANALYSES RECORDED" text="Completed analyses will appear here after a successful authenticated run." />}</>
}

export function AnalyticsPage() {
  const [items, setItems] = useState<AnalysisSummary[]>([]); const [error, setError] = useState('')
  useEffect(() => { api.analyses().then(setItems).catch(e => setError(e.message)) }, [])
  const total = items.reduce((sum, item) => sum + item.detection_count, 0); const average = items.length ? (total / items.length).toFixed(1) : '0'
  const models = useMemo(() => [...new Set(items.map(i => `${i.model_name} ${i.model_version}`))], [items])
  return <><PageHeader index="04" eyebrow="RETAIL TELEMETRY" title="Turn scans into signals." description="Metrics below are calculated only from real stored analysis records. Empty datasets remain empty." />{error && <ErrorNotice message={error} />}<section className="analytics-grid"><article className="panel"><div className="panel-label">DETECTION / VOLUME</div><div className="big-zero">{total}</div><p>Total detections across {items.length} stored analyses.</p></article><article className="panel"><div className="panel-label">DETECTION / AVERAGE</div><div className="big-zero">{average}</div><p>Average detections per stored analysis.</p></article><article className="panel"><div className="panel-label">MODEL / RUNTIME</div><div className="analytics-list">{models.length ? models.map(model => <span key={model}>{model}</span>) : <span>NO DATA</span>}</div><p>Model versions represented in the current dataset.</p></article><article className="panel"><div className="panel-label">STOCK / EVIDENCE</div><div className="big-status">NOT CLAIMED</div><p>The current general COCO detector does not provide sufficient evidence for retail stock-level inference.</p></article></section></>
}

export function SettingsPage() {
  const [token, setToken] = useState(getAccessToken()); const [saved, setSaved] = useState(false)
  const save = () => { setAccessToken(token); setSaved(true); setTimeout(() => setSaved(false), 1800) }
  return <><PageHeader index="05" eyebrow="SYSTEM SETTINGS" title="Control the workspace." description="Store the access token locally in this browser so authenticated analysis requests can reach the backend. The token is never committed to the repository." /><section className="panel settings-panel"><div className="setting-row"><div><strong>API endpoint</strong><span>Configured with VITE_API_BASE_URL, defaulting to /api</span></div><code>/api</code></div><div className="setting-row setting-token"><div><strong>Bearer token</strong><span>Required for analysis, history and persistence endpoints.</span></div><input value={token} onChange={e => setToken(e.target.value)} type="password" autoComplete="off" placeholder="Paste JWT access token" aria-label="JWT access token" /><button className="secondary-button" type="button" onClick={save}>{saved ? 'SAVED' : 'SAVE LOCALLY'}</button></div><div className="setting-row"><div><strong>Vision model</strong><span>YOLOX-Tiny · official ONNX runtime integration</span></div><code>0.1.1RC0</code></div><div className="setting-row"><div><strong>Storage</strong><span>Uploaded images are processed temporarily; persistent image storage is not enabled.</span></div><code>LOCAL TEMP</code></div></section></>
}
