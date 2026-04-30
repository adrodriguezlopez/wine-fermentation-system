"use client"
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ActionSchema, type ActionFormData, ACTION_TYPES, ACTION_TYPE_LABEL } from '@wine/ui'
import type { ActionType } from '@wine/ui'
import { useRecordAction } from '@/hooks'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

interface Props { fermentationId: number }

export function RecordActionForm({ fermentationId }: Props) {
  const { mutateAsync, isPending } = useRecordAction()
  const form = useForm<ActionFormData>({
    resolver: zodResolver(ActionSchema),
    defaultValues: { action_type: 'PUMP_OVER', description: '', taken_at: new Date().toISOString() },
  })

  async function onSubmit(data: ActionFormData) {
    await mutateAsync({ fermentationId, data: data as Record<string, unknown> })
    form.reset({ action_type: data.action_type, description: '', taken_at: new Date().toISOString() })
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3">
        <FormField control={form.control} name="action_type" render={({ field }) => (
          <FormItem>
            <FormLabel>Action Type</FormLabel>
            <Select value={field.value} onValueChange={field.onChange}>
              <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
              <SelectContent>
                {ACTION_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>{ACTION_TYPE_LABEL[t as ActionType]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )} />
        <FormField control={form.control} name="description" render={({ field }) => (
          <FormItem>
            <FormLabel>Description</FormLabel>
            <FormControl><Textarea placeholder="Describe the action taken..." {...field} /></FormControl>
            <FormMessage />
          </FormItem>
        )} />
        <Button type="submit" disabled={isPending}>{isPending ? 'Recording...' : 'Record Action'}</Button>
      </form>
    </Form>
  )
}
