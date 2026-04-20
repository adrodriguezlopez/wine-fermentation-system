// Values match backend SampleType enum (lowercase strings)
export const SAMPLE_TYPES = [
  'sugar',
  'temperature',
  'density',
  'acetic_acid',
] as const

export type SampleTypeKey = (typeof SAMPLE_TYPES)[number]

export const SAMPLE_TYPE_LABEL: Record<SampleTypeKey, string> = {
  sugar: 'Sugar',
  temperature: 'Temperature',
  density: 'Density',
  acetic_acid: 'Acetic Acid',
}

export const SAMPLE_TYPE_UNIT: Record<SampleTypeKey, string> = {
  sugar: '°Bx',
  temperature: '°C',
  density: 'g/cm³',
  acetic_acid: 'g/L',
}
