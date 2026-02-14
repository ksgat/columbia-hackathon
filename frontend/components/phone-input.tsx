"use client"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"

interface PhoneInputProps {
  phones: string[]
  onChange: (phones: string[]) => void
  placeholder?: string
}

export function PhoneInput({ phones, onChange, placeholder = "Phone number" }: PhoneInputProps) {
  const [currentInput, setCurrentInput] = useState("")

  const addPhone = () => {
    if (currentInput.trim() && !phones.includes(currentInput.trim())) {
      onChange([...phones, currentInput.trim()])
      setCurrentInput("")
    }
  }

  const removePhone = (phoneToRemove: string) => {
    onChange(phones.filter(p => p !== phoneToRemove))
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      addPhone()
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Input
          type="tel"
          value={currentInput}
          onChange={(e) => setCurrentInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          className="flex-1 h-10"
        />
        <Button 
          type="button"
          variant="outline"
          onClick={addPhone}
          disabled={!currentInput.trim()}
          className="size-10 text-lg font-semibold"
        >
          +
        </Button>
      </div>

      {phones.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {phones.map((phone) => (
            <div
              key={phone}
              className="flex items-center gap-2 rounded-md bg-muted border border-border px-2.5 py-1.5 text-sm font-medium"
            >
              <span>{phone}</span>
              <button
                type="button"
                onClick={() => removePhone(phone)}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
