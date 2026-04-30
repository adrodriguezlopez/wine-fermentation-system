"use client"
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { SampleSchema, type SampleFormData } from '@wine/ui'
import { SAMPLE_TYPES, SAMPLE_TYPE_LABEL, SAMPLE_TYPE_UNIT } from '@wine/ui'
import { useRecordSample } from '@/hooks'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface Props { fermentationId: number }

export function RecordSampleForm({ fermentationId }: Props) {
  const { mutateAsync, isPending } = useRecordSample()
  const form = useForm<SampleFormData>({
    resolver: zodResolver(SampleSchema),
    defaultValues: {
      sample_type: 'density',
      value: undefined,
      units: SAMPLE_TYPE_UNIT['density'],
      recorded_at: new Date().toISOString(),
    },
  })
  const selectedType = form.watch('sample_type')

  async function onSubmit(data: SampleFormData) {
    await mutateAsync({ fermentationId, data: { ...data, units: SAMPLE_TYPE_UNIT[data.sample_type] } })
    form.reset({ sample_type: data.sample_type, value: undefined, units: SAMPLE_TYPE_UNIT[data.sample_type], recorded_at: new Date().toISOString() })
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3">
        <FormField control={form.control} name="sample_type" render={({ field }) => (
          <FormItem>
            <FormLabel>Sample Type</FormLabel>
            <Select value={field.value} onValueChange={(v) => { field.onChange(v); form.setValue('units', SAMPLE_TYPE_UNIT[v as typeof SAMPLE_TYPES[number]]) }}>
              <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
              <SelectContent>
                {SAMPLE_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>{SAMPLE_TYPE_LABEL[t]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )} />
        <FormField control={form.control} name="value" render={({ field }) => (
          <FormItem>
            <FormLabel>{SAMPLE_TYPE_LABEL[selectedType]} ({SAMPLE_TYPE_UNIT[selectedType]})</FormLabel>
            <FormControl>
              <Input type="number" step="0.001" placeholder={`Enter ${SAMPLE_TYPE_LABEL[selectedType].toLowerCase()} value`}
                {...field} onChange={(e) => field.onChange(parseFloat(e.target.value))} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )} />
        <Button type="submit" disabled={isPending}>{isPending ? 'Recording...' : 'Record Sample'}</Button>
      </form>
    </Form>
  )
}
