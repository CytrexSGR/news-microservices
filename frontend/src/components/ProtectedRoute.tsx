import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useEffect } from 'react'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { status, initializeAuth } = useAuthStore()

  useEffect(() => {
    if (status === 'idle') {
      initializeAuth()
    }
  }, [status, initializeAuth])

  // Show loading state while checking authentication
  if (status === 'idle' || status === 'loading') {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-foreground">Loading...</div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (status === 'unauthenticated') {
    return <Navigate to="/login" replace />
  }

  // Render protected content
  return <>{children}</>
}
