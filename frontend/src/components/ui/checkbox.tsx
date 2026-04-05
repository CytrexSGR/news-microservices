/**
 * Checkbox Component (Temporary Wrapper)
 * TODO: Replace with shadcn/ui checkbox when available
 */
import React from 'react'

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className = '', checked, onCheckedChange, onChange, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange?.(e)
      onCheckedChange?.(e.target.checked)
    }

    return (
      <input
        ref={ref}
        type="checkbox"
        checked={checked}
        onChange={handleChange}
        className={`h-4 w-4 rounded border-gray-300 text-primary focus:ring-2 focus:ring-primary ${className}`}
        {...props}
      />
    )
  }
)

Checkbox.displayName = 'Checkbox'
