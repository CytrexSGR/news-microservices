/**
 * Strategy Editor Page
 *
 * Main page for editing trading strategies
 * Layout: Fixed Header + Sidebar (280px) + Main Panel (flex)
 *
 * Architecture:
 * - 6 main editor modules
 * - Sidebar navigation (EditorSidebar)
 * - Regime-tabs within Entry/Exit/Risk modules
 * - React Hook Form + Zod validation
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { strategyLabClient } from '@/lib/api/strategyLab'
import { Button } from '@/components/ui/Button'
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb'
import { Badge } from '@/components/ui/badge'
import { ChevronLeft, Save, X as XIcon, Eye } from 'lucide-react'
import { EditorSidebar, type EditorSection } from '../components/editor/EditorSidebar'
import { MetadataEditor } from '../components/editor/MetadataEditor'
import { RegimeDetectionEditor } from '../components/editor/RegimeDetectionEditor'
import { MTFAEditor } from '../components/editor/MTFAEditor'
import { ProtectionsEditor } from '../components/editor/ProtectionsEditor'
import { EntryLogicEditor } from '../components/editor/EntryLogicEditor'
import { ExitLogicEditor } from '../components/editor/ExitLogicEditor'
import { RiskManagementEditor } from '../components/editor/RiskManagementEditor'
import { StrategyFormSchema, type StrategyFormValues } from '../schemas/strategySchema'
import { backendToFrontend, frontendToBackend, type BackendStrategyDefinition } from '../utils/strategyFormatConverter'
import toast from 'react-hot-toast'

export default function StrategyEditorPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeSection, setActiveSection] = useState<EditorSection>('metadata')

  // React Hook Form setup
  const form = useForm<StrategyFormValues>({
    resolver: zodResolver(StrategyFormSchema),
    defaultValues: {
      name: '',
      version: '1.0.0',
      description: '',
      author: '',
      tags: [],
      is_public: false,
      definition: {},
    },
  })

  // Fetch strategy
  const { data: strategy, isLoading, error } = useQuery({
    queryKey: ['strategy', id],
    queryFn: () => strategyLabClient.strategy.get(id!),
    enabled: !!id,
  })

  // Populate form when strategy loads
  useEffect(() => {
    if (strategy && strategy.definition) {
      // Convert backend format (nested logic) to frontend format (flat) if needed
      let frontendDefinition = strategy.definition

      // Check if definition is in backend format (has 'logic' field)
      if ('logic' in strategy.definition && strategy.definition.logic) {
        console.log('Converting backend format to frontend format...')
        frontendDefinition = backendToFrontend(strategy.definition as BackendStrategyDefinition)
      }

      form.reset({
        name: strategy.name,
        version: strategy.version,
        description: strategy.description || '',
        author: strategy.author || '',
        tags: strategy.tags || [],
        is_public: strategy.is_public,
        definition: frontendDefinition,
      })
    }
  }, [strategy, form])

  // Watch form values for live updates
  const formValues = form.watch()

  // Create a merged strategy object with form values
  // Deep merge form definition with strategy definition to preserve nested updates
  const currentStrategy = strategy ? {
    ...strategy,
    ...formValues,
    definition: {
      ...(strategy.definition || {}),
      ...(formValues.definition || {}),
    },
  } : null

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: (data: StrategyFormValues) => {
      // Convert frontend format (flat) to backend format (nested logic) before saving
      console.log('Converting frontend format to backend format for save...')
      const backendDefinition = frontendToBackend(
        data.definition as any,
        strategy?.definition as BackendStrategyDefinition
      )

      // Map StrategyFormValues to UpdateStrategyRequest
      const updateRequest = {
        name: data.name,
        version: data.version,
        description: data.description,
        author: data.author,
        tags: data.tags,
        is_public: data.is_public,
        definition: backendDefinition,
      }
      return strategyLabClient.strategy.update(id!, updateRequest as any)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategy', id] })
      queryClient.invalidateQueries({ queryKey: ['strategies'] })
      form.reset(form.getValues()) // Mark form as pristine
      toast.success('Strategy saved successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to save: ${error.message || 'Unknown error'}`)
    },
  })

  // Handle field changes
  const handleFieldChange = (field: string, value: any) => {
    // Update the specific field using React Hook Form
    form.setValue(field as any, value, {
      shouldDirty: true,
      shouldValidate: true
    })
  }

  // Handle save
  const handleSave = form.handleSubmit((data) => {
    saveMutation.mutate(data)
  })

  // Handle cancel
  const handleCancel = () => {
    if (form.formState.isDirty) {
      if (confirm('Discard unsaved changes?')) {
        navigate('/trading/backtest')
      }
    } else {
      navigate('/trading/backtest')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    )
  }

  if (error || !strategy) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <h2 className="text-2xl font-bold mb-4">Strategy Not Found</h2>
        <Button onClick={() => navigate('/trading/backtest')}>
          <ChevronLeft className="h-4 w-4 mr-2" />
          Back to Strategies
        </Button>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Fixed Header */}
      <header className="border-b bg-background px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4 flex-1">
          {/* Breadcrumbs */}
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/trading/backtest">Strategy Lab</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>Edit: {strategy.name}</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>

          {/* Version Badge */}
          <Badge variant="outline">v{strategy.version}</Badge>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleCancel}>
            <XIcon className="h-4 w-4 mr-2" />
            Cancel
          </Button>
          <Button variant="outline" size="sm" onClick={() => toast.info('Preview not implemented yet')}>
            <Eye className="h-4 w-4 mr-2" />
            Preview
          </Button>
          <Button size="sm" onClick={handleSave}>
            <Save className="h-4 w-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </header>

      {/* Main Layout: Sidebar + Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <EditorSidebar activeSection={activeSection} onSectionChange={setActiveSection} />

        {/* Main Panel */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">
            {/* Render active section */}
            {activeSection === 'metadata' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold">Metadata</h2>
                  <p className="text-muted-foreground mt-1">
                    Configure basic strategy information
                  </p>
                </div>
                <MetadataEditor
                  strategy={currentStrategy}
                  onChange={handleFieldChange}
                />
              </div>
            )}

            {activeSection === 'regime-detection' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold">Regime Detection</h2>
                  <p className="text-muted-foreground mt-1">
                    Configure how market regimes are identified
                  </p>
                </div>
                <RegimeDetectionEditor
                  strategy={currentStrategy}
                  onChange={handleFieldChange}
                />
              </div>
            )}

            {activeSection === 'entry-logic' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold">Entry Logic</h2>
                  <p className="text-muted-foreground mt-1">
                    Define entry conditions for each market regime
                  </p>
                </div>
                <EntryLogicEditor
                  strategy={currentStrategy}
                  onChange={handleFieldChange}
                />
              </div>
            )}

            {activeSection === 'exit-logic' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold">Exit Logic</h2>
                  <p className="text-muted-foreground mt-1">
                    Define exit rules for each market regime
                  </p>
                </div>
                <ExitLogicEditor
                  strategy={currentStrategy}
                  onChange={handleFieldChange}
                />
              </div>
            )}

            {activeSection === 'risk-management' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold">Risk Management</h2>
                  <p className="text-muted-foreground mt-1">
                    Configure stop loss, position sizing, and leverage per regime
                  </p>
                </div>
                <RiskManagementEditor
                  strategy={currentStrategy}
                  onChange={handleFieldChange}
                />
              </div>
            )}

            {activeSection === 'mtfa' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold">Multi-Timeframe Analysis</h2>
                  <p className="text-muted-foreground mt-1">
                    Configure timeframe weights and divergence thresholds
                  </p>
                </div>
                <MTFAEditor
                  strategy={currentStrategy}
                  onChange={handleFieldChange}
                />
              </div>
            )}

            {activeSection === 'protections' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold">Protections</h2>
                  <p className="text-muted-foreground mt-1">
                    Configure global safety guards that override all regimes
                  </p>
                </div>
                <ProtectionsEditor
                  strategy={currentStrategy}
                  onChange={handleFieldChange}
                />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
