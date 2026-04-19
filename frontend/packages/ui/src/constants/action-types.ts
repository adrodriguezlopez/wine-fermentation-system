import { ActionType } from '../schemas/action.schema'

export const ACTION_TYPE_LABEL: Record<ActionType, string> = {
  TEMPERATURE_ADJUSTMENT: 'Temperature Adjustment',
  NUTRIENT_ADDITION: 'Nutrient Addition',
  SULFUR_ADDITION: 'Sulfur Addition',
  PUMP_OVER: 'Pump Over',
  PUNCH_DOWN: 'Punch Down',
  RACK: 'Rack',
  FILTRATION: 'Filtration',
  YEAST_ADDITION: 'Yeast Addition',
  H2S_TREATMENT: 'H₂S Treatment',
  STUCK_FERMENTATION_PROTOCOL: 'Stuck Fermentation Protocol',
  PROTOCOL_STEP_COMPLETED_LATE: 'Protocol Step Completed Late',
  CUSTOM: 'Custom',
}
