import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground border-input w-full min-w-0 rounded-lg border bg-background px-3.5 py-2 text-sm font-medium transition-all outline-none disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-40",
        "focus:border-ring focus:ring-2 focus:ring-ring/10",
        "aria-invalid:ring-destructive/20 aria-invalid:border-destructive",
        "resize-none",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
