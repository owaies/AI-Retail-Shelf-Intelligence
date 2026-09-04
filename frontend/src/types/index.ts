export type ApiHealth = {
  status: 'ok' | 'degraded' | 'error'
  service: string
}

export type AnalysisStatus = 'ready' | 'processing' | 'complete' | 'partial' | 'failed'

export type DetectionResult = {
  class_name: string
  confidence: number
  box: { x: number; y: number; width: number; height: number }
}

export type ShelfAssessment = {
  status: string
  object_coverage: number
  low_stock_supported: boolean
  note: string
}

export type Analysis = {
  id: string
  user_id: string
  image_name: string
  status: AnalysisStatus
  image_width: number
  image_height: number
  detection_count: number
  class_counts: Record<string, number>
  detections: DetectionResult[]
  shelf_assessment: ShelfAssessment
  shelf_regions: Array<{ label: string; status: string; confidence: number | null; box: DetectionResult['box'] }>
  model_name: string
  model_version: string
  created_at: string
  completed_at: string | null
}

export type AnalysisSummary = Pick<Analysis, 'id' | 'status' | 'created_at' | 'image_name' | 'detection_count' | 'model_name' | 'model_version'>
