"use client"

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import { CreateFermentationSchema, type CreateFermentationData } from '@wine/ui'
import { useCreateFermentation, useProtocols } from '@/hooks'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export function CreateFermentationForm() {
  const router = useRouter()
  const { mutateAsync, isPending, error } = useCreateFermentation()
  const { data: protocolsData } = useProtocols()
  const protocols = protocolsData?.items ?? []

  const form = useForm<CreateFermentationData>({
    resolver: zodResolver(CreateFermentationSchema),
    defaultValues: {
      vintage_year: new Date().getFullYear(),
      yeast_strain: '',
      vessel_code: '',
      input_mass_kg: undefined,
      initial_sugar_brix: undefined,
      initial_density: undefined,
      start_date: new Date().toISOString(),
    },
  })

  async function onSubmit(data: CreateFermentationData) {
    try {
      const result = await mutateAsync(data as Record<string, unknown>)
      router.push(`/fermentations/${result.id}`)
    } catch {
      // error is displayed via the `error` state from useMutation
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {(error as Error).message}
          </div>
        )}

        <FormField
          control={form.control}
          name="vintage_year"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Vintage Year</FormLabel>
              <FormControl>
                <Input type="number" {...field} onChange={(e) => field.onChange(parseInt(e.target.value, 10))} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="yeast_strain"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Yeast Strain</FormLabel>
              <FormControl>
                <Input placeholder="e.g. EC-1118" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="vessel_code"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Vessel Code (optional)</FormLabel>
              <FormControl>
                <Input placeholder="e.g. VAT-01" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="input_mass_kg"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Input Mass (kg)</FormLabel>
              <FormControl>
                <Input type="number" step="0.1" {...field} onChange={(e) => field.onChange(parseFloat(e.target.value))} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="initial_sugar_brix"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Initial Sugar (°Bx)</FormLabel>
              <FormControl>
                <Input type="number" step="0.1" {...field} onChange={(e) => field.onChange(parseFloat(e.target.value))} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="initial_density"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Initial Density (g/cm³)</FormLabel>
              <FormControl>
                <Input type="number" step="0.001" {...field} onChange={(e) => field.onChange(parseFloat(e.target.value))} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div>
          <label className="text-sm font-medium">Protocol (optional)</label>
          <Select onValueChange={() => {}}>
            <SelectTrigger>
              <SelectValue placeholder="No protocol (assign later)" />
            </SelectTrigger>
            <SelectContent>
              {protocols.map((p) => (
                <SelectItem key={p.id} value={String(p.id)}>
                  {p.protocol_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button type="submit" disabled={isPending}>
          {isPending ? 'Creating...' : 'Create Fermentation'}
        </Button>
      </form>
    </Form>
  )
}
