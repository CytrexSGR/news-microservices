/**
 * EditorSidebar Component
 *
 * Fixed-width sidebar navigation for Strategy Editor
 * Shows 6 main modules with icons and active state
 */

import { cn } from '@/lib/utils'
import {
  FileText,
  TrendingUp,
  ArrowRight,
  X,
  Shield,
  Layers,
  Lock,
} from 'lucide-react'

export type EditorSection =
  | 'metadata'
  | 'regime-detection'
  | 'entry-logic'
  | 'exit-logic'
  | 'risk-management'
  | 'mtfa'
  | 'protections'

interface EditorSidebarProps {
  activeSection: EditorSection
  onSectionChange: (section: EditorSection) => void
}

const navigationItems: Array<{
  id: EditorSection
  label: string
  icon: typeof FileText
  description: string
}> = [
  {
    id: 'metadata',
    label: 'Metadata',
    icon: FileText,
    description: 'Basic strategy information',
  },
  {
    id: 'regime-detection',
    label: 'Regime Detection',
    icon: TrendingUp,
    description: 'Market phase identification',
  },
  {
    id: 'entry-logic',
    label: 'Entry Logic',
    icon: ArrowRight,
    description: 'Entry conditions per regime',
  },
  {
    id: 'exit-logic',
    label: 'Exit Logic',
    icon: X,
    description: 'Exit rules per regime',
  },
  {
    id: 'risk-management',
    label: 'Risk Management',
    icon: Shield,
    description: 'Stop loss, position size, leverage',
  },
  {
    id: 'mtfa',
    label: 'Multi-Timeframe',
    icon: Layers,
    description: 'Timeframe analysis config',
  },
  {
    id: 'protections',
    label: 'Protections',
    icon: Lock,
    description: 'Global safety guards',
  },
]

export function EditorSidebar({ activeSection, onSectionChange }: EditorSidebarProps) {
  return (
    <aside className="w-[280px] border-r bg-muted/30 p-4 overflow-y-auto">
      <div className="space-y-1">
        {navigationItems.map((item) => {
          const Icon = item.icon
          const isActive = activeSection === item.id

          return (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={cn(
                'w-full flex items-start gap-3 px-3 py-2.5 rounded-md transition-colors text-left',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted text-muted-foreground hover:text-foreground'
              )}
            >
              <Icon className={cn('h-5 w-5 mt-0.5 flex-shrink-0', isActive && 'text-primary-foreground')} />
              <div className="flex-1 min-w-0">
                <div className={cn('font-medium text-sm', isActive && 'text-primary-foreground')}>
                  {item.label}
                </div>
                <div
                  className={cn(
                    'text-xs mt-0.5',
                    isActive ? 'text-primary-foreground/80' : 'text-muted-foreground'
                  )}
                >
                  {item.description}
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </aside>
  )
}
