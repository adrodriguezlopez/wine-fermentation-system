---
name: shadcn-ui
description: Use when adding shadcn/ui components, customizing them, or building UI with Radix primitives and Tailwind in a Next.js or React project
---

# shadcn/ui

## Overview

shadcn/ui is **not a package** — it's a CLI that copies component source code into your project. Components live in `src/components/ui/` and are fully yours to modify.

## Install a Component

```bash
# From the app directory:
npx shadcn@latest add button
npx shadcn@latest add card dialog input select table badge
```

Components land in `components/ui/button.tsx`, etc.

## Usage

```tsx
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function FermentationCard({ name, status }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{name}</CardTitle>
      </CardHeader>
      <CardContent>
        <Badge variant="outline">{status}</Badge>
        <Button variant="default" size="sm">View Details</Button>
      </CardContent>
    </Card>
  );
}
```

## Button Variants

```tsx
<Button variant="default">Primary</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Secondary</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="link">Link</Button>
<Button size="sm" | "default" | "lg" | "icon" />
```

## Customizing Components

Edit the file directly — it's your code:

```tsx
// components/ui/button.tsx — add a wine variant
const buttonVariants = cva(
  "inline-flex items-center ...",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground ...",
        wine: "bg-[#8B1A2E] text-white hover:bg-[#6B1422]",  // ← add this
        // ...
      },
    },
  }
);
```

## Tailwind CSS Variables (globals.css)

shadcn uses CSS variables for theming. Override in `globals.css`:

```css
@layer base {
  :root {
    --background: 0 0% 98%;          /* #FAFAF8 */
    --foreground: 240 30% 14%;       /* #1A1A2E */
    --primary: 350 69% 32%;          /* #8B1A2E wine red */
    --primary-foreground: 0 0% 100%;
    --card: 0 0% 100%;
    --border: 0 0% 90%;
    --radius: 0.5rem;
  }
}
```

## Form with React Hook Form + Zod

shadcn/ui `Form` component wraps React Hook Form:

```bash
npx shadcn@latest add form input label
```

```tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const schema = z.object({ name: z.string().min(1, "Required") });

export function CreateForm({ onSubmit }) {
  const form = useForm({ resolver: zodResolver(schema) });
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl><Input {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Create</Button>
      </form>
    </Form>
  );
}
```

## Dialog

```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

<Dialog>
  <DialogTrigger asChild>
    <Button>Open</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Create Fermentation</DialogTitle>
    </DialogHeader>
    {/* form content */}
  </DialogContent>
</Dialog>
```

## Table

```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Batch</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {rows.map(row => (
      <TableRow key={row.id}>
        <TableCell>{row.name}</TableCell>
        <TableCell><Badge>{row.status}</Badge></TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `import { Button } from "shadcn/ui"` | Components live in `@/components/ui/button` |
| Trying to override via npm | Edit the file in `components/ui/` directly |
| Missing `cn()` utility | Import from `@/lib/utils`: `import { cn } from "@/lib/utils"` |
| Forgetting `asChild` on Dialog trigger | `<DialogTrigger asChild>` passes props to child element |
