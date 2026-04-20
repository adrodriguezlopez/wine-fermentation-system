export const SAMPLE_TYPES = [
  'DENSITY',
  'TEMPERATURE_CELSIUS',
  'GLUCOSE',
  'ETHANOL',
  'ACETIC_ACID',
  'MALIC_ACID',
  'PH',
  'SO2',
  'TURBIDITY',
  'COLOR_INTENSITY',
  'VOLATILE_ACIDITY',
] as const

export type SampleTypeKey = (typeof SAMPLE_TYPES)[number]

export const SAMPLE_TYPE_LABEL: Record<SampleTypeKey, string> = {
  DENSITY: 'Density',
  TEMPERATURE_CELSIUS: 'Temperature',
  GLUCOSE: 'Glucose',
  ETHANOL: 'Ethanol',
  ACETIC_ACID: 'Acetic Acid',
  MALIC_ACID: 'Malic Acid',
  PH: 'pH',
  SO2: 'SO₂',
  TURBIDITY: 'Turbidity',
  COLOR_INTENSITY: 'Color Intensity',
  VOLATILE_ACIDITY: 'Volatile Acidity',
}

export const SAMPLE_TYPE_UNIT: Record<SampleTypeKey, string> = {
  DENSITY: 'g/cm³',
  TEMPERATURE_CELSIUS: '°C',
  GLUCOSE: 'g/L',
  ETHANOL: '%vol',
  ACETIC_ACID: 'g/L',
  MALIC_ACID: 'g/L',
  PH: '',
  SO2: 'mg/L',
  TURBIDITY: 'NTU',
  COLOR_INTENSITY: 'AU',
  VOLATILE_ACIDITY: 'g/L',
}
