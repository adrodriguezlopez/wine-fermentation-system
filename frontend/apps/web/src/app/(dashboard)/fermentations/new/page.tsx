"use client"

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { CreateFermentationForm } from '@/components/fermentation/create-fermentation-form'

export default function NewFermentationPage() {
  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/fermentations" className="text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-semibold">New Fermentation</h1>
      </div>
      <CreateFermentationForm />
    </div>
  )
}
