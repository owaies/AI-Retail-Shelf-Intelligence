export type ApiHealth = {
  status: 'ok' | 'degraded' | 'error'
  service: string
}

export type AnalysisStatus = 'ready' | 'processing' | 'complete' | 'partial' | 'failed'

export type AnalysisSummary = {
  id: string
  status: AnalysisStatus
  createdAt: string
  imageName: string
  detectionCount: number
}

export type DetectionResult = {
  className: string
  confidence: number
  box: { x: number; y: number; width: number; height: number }
}
