import { describe, it, expectTypeOf } from 'vitest'
import type { FermentationDto, PaginatedResponse } from '../src/types/fermentation'
import type { UserDto } from '../src/types/auth'

describe('FermentationDto', () => {
  it('has required fields', () => {
    expectTypeOf<FermentationDto>().toHaveProperty('id')
    expectTypeOf<FermentationDto>().toHaveProperty('status')
    expectTypeOf<FermentationDto>().toHaveProperty('winery_id')
  })
})

describe('PaginatedResponse', () => {
  it('is generic', () => {
    type T = PaginatedResponse<FermentationDto>
    expectTypeOf<T>().toHaveProperty('items')
    expectTypeOf<T>().toHaveProperty('total')
  })
})

describe('UserDto', () => {
  it('has role and winery_id', () => {
    expectTypeOf<UserDto>().toHaveProperty('role')
    expectTypeOf<UserDto>().toHaveProperty('winery_id')
  })
})
