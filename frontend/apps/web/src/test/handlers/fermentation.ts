import { http, HttpResponse } from 'msw'

const baseFermentation = {
  id: 1,
  winery_id: 1,
  vintage_year: 2024,
  yeast_strain: 'EC-1118',
  vessel_code: 'VAT-01',
  input_mass_kg: 1000,
  initial_sugar_brix: 24.5,
  initial_density: 1.102,
  start_date: '2024-09-01T00:00:00Z',
  status: 'ACTIVE' as const,
  notes: null,
  created_at: '2024-09-01T00:00:00Z',
  updated_at: '2024-09-01T00:00:00Z',
}

const fermentation1 = { ...baseFermentation, id: 1 }
const fermentation2 = {
  ...baseFermentation,
  id: 2,
  vessel_code: 'VAT-02',
  vintage_year: 2022,
  yeast_strain: 'RC-212',
  initial_sugar_brix: 22.0,
  initial_density: 1.092,
}

const sampleDensity = {
  id: 1,
  fermentation_id: 1,
  sample_type: 'density' as const,
  value: 1.095,
  units: 'g/cm3',
  recorded_at: '2024-09-02T10:00:00Z',
  created_at: '2024-09-02T10:00:00Z',
  updated_at: '2024-09-02T10:00:00Z',
}

const sampleTemperature = {
  id: 2,
  fermentation_id: 1,
  sample_type: 'temperature' as const,
  value: 22.5,
  units: '°C',
  recorded_at: '2024-09-02T12:00:00Z',
  created_at: '2024-09-02T12:00:00Z',
  updated_at: '2024-09-02T12:00:00Z',
}

const sampleSugar = {
  id: 3,
  fermentation_id: 1,
  sample_type: 'sugar' as const,
  value: 20.1,
  units: 'Brix',
  recorded_at: '2024-09-02T14:00:00Z',
  created_at: '2024-09-02T14:00:00Z',
  updated_at: '2024-09-02T14:00:00Z',
}

const actionDto = {
  id: 1,
  winery_id: 1,
  taken_by_user_id: 1,
  fermentation_id: 1,
  execution_id: null,
  step_id: null,
  alert_id: null,
  recommendation_id: null,
  action_type: 'PUMP_OVER',
  description: 'Pump over to improve cap management',
  taken_at: '2024-09-02T10:00:00Z',
  outcome: 'SUCCESS',
  outcome_notes: null,
  outcome_recorded_at: null,
  created_at: '2024-09-02T10:00:00Z',
  updated_at: '2024-09-02T10:00:00Z',
}

const alertDto = {
  id: 1,
  execution_id: 1,
  protocol_id: 1,
  winery_id: 1,
  step_id: null,
  step_name: null,
  alert_type: 'TEMPERATURE_HIGH',
  severity: 'WARNING',
  status: 'PENDING',
  message: 'Temperature is above recommended range',
  created_at: '2024-09-02T10:00:00Z',
  sent_at: null,
  acknowledged_at: null,
  dismissed_at: null,
}

const executionDto = {
  id: 1,
  fermentation_id: 1,
  protocol_id: 1,
  winery_id: 1,
  status: 'ACTIVE',
  start_date: '2024-09-01T00:00:00Z',
  completion_percentage: 35,
  compliance_score: 92,
  notes: null,
  created_at: '2024-09-01T00:00:00Z',
  updated_at: '2024-09-02T00:00:00Z',
}

const protocolDto1 = {
  id: 1,
  winery_id: 1,
  varietal_code: 'CAB',
  varietal_name: 'Cabernet Sauvignon',
  color: 'RED',
  version: '1.0',
  protocol_name: 'Standard Cab Protocol',
  is_active: true,
  expected_duration_days: 14,
  description: null,
  is_template: false,
  state: 'APPROVED',
  template_id: null,
  approved_by_user_id: 1,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const protocolDto2 = {
  ...protocolDto1,
  id: 2,
  varietal_code: 'CHARD',
  varietal_name: 'Chardonnay',
  color: 'WHITE',
  protocol_name: 'Standard Chardonnay Protocol',
}

const analysisSummaryDto = {
  id: 'analysis-1',
  fermentation_id: '1',
  status: 'COMPLETE',
  analyzed_at: '2024-09-02T15:00:00Z',
  historical_samples_count: 10,
  anomaly_count: 1,
  recommendation_count: 2,
}

const analysisDto = {
  id: 'analysis-1',
  fermentation_id: '1',
  winery_id: '1',
  status: 'COMPLETE' as const,
  analyzed_at: '2024-09-02T15:00:00Z',
  comparison_result: {},
  confidence_level: {},
  historical_samples_count: 10,
  anomalies: [
    {
      id: 'anomaly-1',
      analysis_id: 'analysis-1',
      anomaly_type: 'TEMPERATURE_SPIKE',
      severity: 'WARNING',
      description: 'Temperature spike detected',
      detected_at: '2024-09-02T10:00:00Z',
    },
  ],
  recommendations: [
    {
      id: 'rec-1',
      analysis_id: 'analysis-1',
      recommendation_type: 'ADJUST_TEMPERATURE',
      priority: 'HIGH',
      description: 'Reduce fermentation temperature',
      applied: false,
      applied_at: null,
    },
    {
      id: 'rec-2',
      analysis_id: 'analysis-1',
      recommendation_type: 'PUMP_OVER',
      priority: 'MEDIUM',
      description: 'Perform pump over',
      applied: false,
      applied_at: null,
    },
  ],
}

const statisticsDto = {
  fermentation_id: 1,
  status: 'ACTIVE',
  start_date: '2024-09-01T00:00:00Z',
  duration_days: 1,
  total_samples: 3,
  samples_by_type: { density: 1, temperature: 1, sugar: 1 },
  initial_sugar: 24.5,
  latest_sugar: 20.1,
  sugar_drop: 4.4,
  avg_temperature: 22.5,
  avg_samples_per_day: 3,
}

const FIXED_TIMESTAMP = '2024-06-15T14:30:00.000Z'

export const fermentationHandlers = [
  // GET /api/fermentation/fermentations/:id/samples/latest  (most specific first)
  http.get('/api/fermentation/fermentations/:id/samples/latest', () => {
    return HttpResponse.json(sampleDensity)
  }),

  // GET /api/fermentation/fermentations/:id/samples
  http.get('/api/fermentation/fermentations/:id/samples', () => {
    return HttpResponse.json([sampleDensity, sampleTemperature, sampleSugar])
  }),

  // POST /api/fermentation/fermentations/:id/samples
  http.post('/api/fermentation/fermentations/:id/samples', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json(
      { ...sampleDensity, id: 99, ...body },
      { status: 201 }
    )
  }),

  // GET /api/fermentation/fermentations/:id/actions
  http.get('/api/fermentation/fermentations/:id/actions', () => {
    return HttpResponse.json({ items: [actionDto], total: 1, skip: 0, limit: 20 })
  }),

  // POST /api/fermentation/fermentations/:id/actions
  http.post('/api/fermentation/fermentations/:id/actions', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json(
      { ...actionDto, id: 99, ...body },
      { status: 201 }
    )
  }),

  // GET /api/fermentation/fermentations/:id/statistics
  http.get('/api/fermentation/fermentations/:id/statistics', ({ params }) => {
    return HttpResponse.json({ ...statisticsDto, fermentation_id: Number(params.id) })
  }),

  // POST /api/fermentation/fermentations/:id/execute
  http.post('/api/fermentation/fermentations/:id/execute', ({ params }) => {
    return HttpResponse.json(
      { ...executionDto, fermentation_id: Number(params.id) },
      { status: 201 }
    )
  }),

  // GET /api/fermentation/fermentations/:id
  http.get('/api/fermentation/fermentations/:id', ({ params }) => {
    const id = Number(params.id)
    return HttpResponse.json({ ...fermentation1, id, execution_id: 1 })
  }),

  // GET /api/fermentation/fermentations
  http.get('/api/fermentation/fermentations', () => {
    return HttpResponse.json({
      items: [fermentation1, fermentation2],
      total: 2,
      page: 1,
      size: 20,
    })
  }),

  // POST /api/fermentation/fermentations
  http.post('/api/fermentation/fermentations', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json(
      { ...fermentation1, id: 99, ...body },
      { status: 201 }
    )
  }),

  // PATCH /api/fermentation/actions/:id/outcome
  http.patch('/api/fermentation/actions/:id/outcome', async ({ params, request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({ ...actionDto, id: Number(params.id), ...body })
  }),

  // GET /api/fermentation/executions/:id/alerts
  http.get('/api/fermentation/executions/:id/alerts', () => {
    return HttpResponse.json({ items: [alertDto], total: 1, pending_count: 1 })
  }),

  // GET /api/fermentation/executions/:id/completions
  http.get('/api/fermentation/executions/:id/completions', () => {
    return HttpResponse.json([
      {
        id: 1,
        execution_id: 1,
        step_id: 1,
        step_name: 'Initial Crush',
        completed_at: '2024-09-01T12:00:00Z',
        notes: null,
      },
    ])
  }),

  // GET /api/fermentation/executions/:id
  http.get('/api/fermentation/executions/:id', ({ params }) => {
    return HttpResponse.json({ ...executionDto, id: Number(params.id) })
  }),

  // POST /api/fermentation/alerts/:id/acknowledge
  http.post('/api/fermentation/alerts/:id/acknowledge', ({ params }) => {
    return HttpResponse.json({
      ...alertDto,
      id: Number(params.id),
      status: 'ACKNOWLEDGED',
      acknowledged_at: FIXED_TIMESTAMP,
    })
  }),

  // POST /api/fermentation/alerts/:id/dismiss
  http.post('/api/fermentation/alerts/:id/dismiss', ({ params }) => {
    return HttpResponse.json({
      ...alertDto,
      id: Number(params.id),
      status: 'DISMISSED',
      dismissed_at: FIXED_TIMESTAMP,
    })
  }),

  // GET /api/fermentation/protocols
  http.get('/api/fermentation/protocols', () => {
    return HttpResponse.json({
      items: [protocolDto1, protocolDto2],
      total_count: 2,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
  }),

  // GET /api/analysis/analyses/fermentation/:id  (more specific first)
  http.get('/api/analysis/analyses/fermentation/:id', () => {
    return HttpResponse.json({
      items: [analysisSummaryDto],
      total: 1,
      page: 1,
      size: 20,
    })
  }),

  // GET /api/analysis/analyses/:id
  http.get('/api/analysis/analyses/:id', ({ params }) => {
    return HttpResponse.json({ ...analysisDto, id: String(params.id) })
  }),

  // POST /api/analysis/analyses
  http.post('/api/analysis/analyses', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json(
      { ...analysisDto, id: 'analysis-new', ...body },
      { status: 201 }
    )
  }),

  // GET /api/analysis/fermentations/:id/advisories
  http.get('/api/analysis/fermentations/:id/advisories', () => {
    return HttpResponse.json([
      {
        id: 'advisory-1',
        fermentation_id: '1',
        advisory_type: 'TEMPERATURE',
        message: 'Consider reducing temperature',
        created_at: '2024-09-02T15:00:00Z',
      },
    ])
  }),

  // PUT /api/analysis/recommendations/:id/apply
  http.put('/api/analysis/recommendations/:id/apply', ({ params }) => {
    return HttpResponse.json({
      ...analysisDto.recommendations[0],
      id: String(params.id),
      applied: true,
      applied_at: FIXED_TIMESTAMP,
    })
  }),
]
