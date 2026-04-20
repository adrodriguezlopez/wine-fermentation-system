import { z } from 'zod'

/**
 * Generic paginated list response — all backend list endpoints return this shape:
 * { items: [...], total: number, page: number, size: number, pages: number }
 */
export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    total: z.number().int().nonnegative(),
    page: z.number().int().positive(),
    size: z.number().int().positive(),
    pages: z.number().int().nonnegative(),
  })

export type PaginatedResponse<T> = {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

/**
 * RFC 7807 Problem Details — all backend error responses use this shape.
 * https://datatracker.ietf.org/doc/html/rfc7807
 */
export const ApiErrorSchema = z.object({
  type: z.string(),
  title: z.string(),
  status: z.number().int(),
  detail: z.string(),
})

export type ApiError = z.infer<typeof ApiErrorSchema>
