export type SampleTypeKey = 'DENSITY' | 'TEMPERATURE' | 'BRIX' | 'ACETIC_ACID'

export const SAMPLE_TYPE_LABEL: Record<SampleTypeKey, string> = {
  DENSITY: 'Density',
  TEMPERATURE: 'Temperature',
  BRIX: 'Brix',
  ACETIC_ACID: 'Acetic Acid',
}

export const SAMPLE_TYPE_UNIT: Record<SampleTypeKey, string> = {
  DENSITY: 'g/cm³',
  TEMPERATURE: '°C',
  BRIX: '°Bx',
  ACETIC_ACID: 'g/L',
}
