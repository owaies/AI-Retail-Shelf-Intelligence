function PageHeader({ index, eyebrow, title, description }: { index: string; eyebrow: string; title: string; description: string }) {
  return (
    <section className="page-header">
      <div className="eyebrow"><span>{index}</span>{eyebrow}</div>
      <h1>{title}</h1>
      <p>{description}</p>
    </section>
  )
}

function EmptyPanel({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-panel">
      <span className="cross" aria-hidden="true">+</span>
      <strong>{title}</strong>
      <p>{text}</p>
    </div>
  )
}

export function DashboardPage() {
  return (
    <>
      <PageHeader index="01" eyebrow="COMMAND CENTER" title="Shelf intelligence." description="A focused workspace for turning shelf imagery into measurable retail observations." />
      <section className="hero-grid">
        <article className="panel hero-panel">
          <div className="panel-label">VISION / READY</div>
          <h2>See the shelf.<br /><span>Know the shelf.</span></h2>
          <p>Upload an image to begin computer-vision analysis. Detection and shelf-status intelligence will appear here once the vision pipeline is connected.</p>
          <a className="primary-button" href="/analyze">START ANALYSIS <span>↗</span></a>
        </article>
        <div className="metric-stack" aria-label="Foundation metrics">
          <article className="metric-card"><span>ANALYSES</span><strong>0</strong><small>Awaiting first image</small></article>
          <article className="metric-card accent"><span>DETECTIONS</span><strong>0</strong><small>No inference run yet</small></article>
          <article className="metric-card"><span>SYSTEM</span><strong>OK</strong><small>API foundation online</small></article>
        </div>
      </section>
      <section className="section-block">
        <div className="section-heading"><div><span className="panel-label">RECENT / ANALYSIS LOG</span><h2>Recent analyses</h2></div><span className="mono">NO RUNS YET</span></div>
        <EmptyPanel title="READY FOR FIRST ANALYSIS" text="Upload a shelf image to create your first analysis record." />
      </section>
    </>
  )
}

export function AnalyzePage() {
  return (
    <>
      <PageHeader index="02" eyebrow="SHELF ANALYSIS" title="Read the shelf." description="Prepare an image for the vision pipeline. Actual inference will be connected in Day 2." />
      <section className="analysis-workspace">
        <article className="panel upload-panel">
          <div className="panel-label">INPUT / IMAGE</div>
          <div className="upload-zone" tabIndex={0} role="button" aria-label="Shelf image upload area">
            <div className="scan-icon" aria-hidden="true">⌁</div>
            <h2>Upload shelf image</h2>
            <p>JPEG, PNG or WebP · maximum size enforced by the backend</p>
            <span className="secondary-button">CHOOSE IMAGE</span>
          </div>
        </article>
        <aside className="panel status-panel">
          <div className="panel-label">PIPELINE / STATUS</div>
          <ol className="pipeline">
            {['Validate image', 'Preprocess with OpenCV', 'Run YOLO inference', 'Analyze shelf regions', 'Store result'].map((step, index) => (
              <li key={step}><span>{String(index + 1).padStart(2, '0')}</span><strong>{step}</strong><small>PLANNED</small></li>
            ))}
          </ol>
          <div className="notice"><strong>READY</strong><p>No image is being processed. This screen does not generate mock detections.</p></div>
        </aside>
      </section>
    </>
  )
}

export function HistoryPage() {
  return <><PageHeader index="03" eyebrow="ANALYSIS HISTORY" title="Every scan, traceable." description="Historical analysis records will become available after the backend persistence layer is implemented." /><EmptyPanel title="NO ANALYSES RECORDED" text="Completed shelf analyses will appear here with image, status, detection count and timestamp." /></>
}

export function AnalyticsPage() {
  return <><PageHeader index="04" eyebrow="RETAIL TELEMETRY" title="Turn scans into signals." description="Analytics will summarize real stored analyses. No fabricated metrics are shown in the foundation build." /><section className="analytics-grid"><article className="panel"><div className="panel-label">DETECTION / VOLUME</div><div className="big-zero">0</div><p>Total detections from completed analyses.</p></article><article className="panel"><div className="panel-label">SHELF / STATUS</div><div className="signal-line"><span /><span /><span /><span /></div><p>Awaiting real shelf observations.</p></article></section></>
}

export function SettingsPage() {
  return <><PageHeader index="05" eyebrow="SYSTEM SETTINGS" title="Control the workspace." description="Configuration will be added as backend, storage and model settings become available." /><section className="panel settings-panel"><div className="setting-row"><div><strong>API endpoint</strong><span>Configured through environment variables</span></div><code>/api</code></div><div className="setting-row"><div><strong>Vision model</strong><span>Not integrated in Day 1</span></div><code>DAY 2</code></div><div className="setting-row"><div><strong>Storage</strong><span>Architecture prepared for managed object storage</span></div><code>PLANNED</code></div></section></>
}
