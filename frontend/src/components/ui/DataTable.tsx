import { type ReactNode, useState, useMemo } from 'react'
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'

export interface Column<T> {
  header: string
  accessor: keyof T | ((row: T) => ReactNode)
  cell?: (value: any, row: T) => ReactNode
  sortKey?: string
  sortFn?: (a: T, b: T) => number
}

interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  keyExtractor: (row: T) => string
}

type SortDirection = 'asc' | 'desc' | null

export function DataTable<T>({ data, columns, keyExtractor }: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)

  const handleSort = (column: Column<T>) => {
    if (!column.sortKey && !column.sortFn) return

    const key = column.sortKey || column.header

    if (sortKey === key) {
      // Cycle through: asc -> desc -> null
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortDirection(null)
        setSortKey(null)
      }
    } else {
      setSortKey(key)
      setSortDirection('asc')
    }
  }

  const sortedData = useMemo(() => {
    if (!sortKey || !sortDirection) return data

    const column = columns.find(col => (col.sortKey || col.header) === sortKey)
    if (!column) return data

    return [...data].sort((a, b) => {
      // Use custom sort function if provided
      if (column.sortFn) {
        const result = column.sortFn(a, b)
        return sortDirection === 'asc' ? result : -result
      }

      // Default sorting logic
      let aValue: any
      let bValue: any

      if (typeof column.accessor === 'function') {
        // For function accessors, we can't sort directly
        // Skip or handle specially
        return 0
      } else {
        aValue = a[column.accessor]
        bValue = b[column.accessor]
      }

      // Handle null/undefined
      if (aValue == null && bValue == null) return 0
      if (aValue == null) return 1
      if (bValue == null) return -1

      // String comparison (case-insensitive)
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.toLowerCase().localeCompare(bValue.toLowerCase())
        return sortDirection === 'asc' ? comparison : -comparison
      }

      // Number comparison
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
      }

      // Date comparison
      if (aValue instanceof Date && bValue instanceof Date) {
        return sortDirection === 'asc'
          ? aValue.getTime() - bValue.getTime()
          : bValue.getTime() - aValue.getTime()
      }

      return 0
    })
  }, [data, sortKey, sortDirection, columns])

  const getSortIcon = (column: Column<T>) => {
    if (!column.sortKey && !column.sortFn) return null

    const key = column.sortKey || column.header
    const isActive = sortKey === key

    if (!isActive) {
      return <ArrowUpDown className="ml-2 h-4 w-4 opacity-30" />
    }

    return sortDirection === 'asc'
      ? <ArrowUp className="ml-2 h-4 w-4" />
      : <ArrowDown className="ml-2 h-4 w-4" />
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full">
        <thead className="bg-muted">
          <tr>
            {columns.map((column, index) => {
              const isSortable = column.sortKey || column.sortFn
              return (
                <th
                  key={index}
                  className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground ${
                    isSortable ? 'cursor-pointer hover:bg-muted-foreground/10 select-none' : ''
                  }`}
                  onClick={() => isSortable && handleSort(column)}
                >
                  <div className="flex items-center">
                    {column.header}
                    {getSortIcon(column)}
                  </div>
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-card">
          {sortedData.map((row) => (
            <tr key={keyExtractor(row)} className="hover:bg-muted/50 transition-colors">
              {columns.map((column, index) => {
                let cellContent: ReactNode

                if (typeof column.accessor === 'function') {
                  cellContent = column.accessor(row)
                } else {
                  const value = row[column.accessor]
                  cellContent = column.cell ? column.cell(value, row) : String(value ?? '')
                }

                return (
                  <td key={index} className="px-6 py-4 text-sm text-foreground">
                    {cellContent}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
