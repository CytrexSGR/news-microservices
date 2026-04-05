import axios, { AxiosError, type AxiosInstance } from 'axios'
import toast from 'react-hot-toast'

class ApiClient {
  private client: AxiosInstance

  constructor(baseURL: string, timeout: number = 30000) {
    this.client = axios.create({
      baseURL,
      timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        this.handleError(error)
        return Promise.reject(error)
      }
    )
  }

  private handleError(error: AxiosError) {
    if (error.response) {
      const status = error.response.status
      const detail = (error.response.data as any)?.detail

      // Format error message based on detail type
      let message: string
      if (Array.isArray(detail)) {
        // Pydantic validation errors (array of error objects)
        message = detail.map((err: any) => {
          const field = err.loc?.join('.') || 'unknown'
          return `${field}: ${err.msg}`
        }).join(', ')
      } else if (typeof detail === 'string') {
        message = detail
      } else {
        message = error.message
      }

      if (status === 401) {
        toast.error('Authentication required')
        // Redirect to login if needed
      } else if (status === 403) {
        toast.error('Access denied')
      } else if (status === 404) {
        toast.error('Resource not found')
      } else if (status >= 500) {
        toast.error('Server error - please try again')
      } else {
        toast.error(message)
      }
    } else if (error.request) {
      toast.error('Network error - check your connection')
    } else {
      toast.error(error.message)
    }
  }

  get<T>(url: string, params?: any) {
    return this.client.get<T>(url, { params })
  }

  post<T>(url: string, data?: any) {
    return this.client.post<T>(url, data)
  }

  put<T>(url: string, data?: any) {
    return this.client.put<T>(url, data)
  }

  delete<T>(url: string) {
    return this.client.delete<T>(url)
  }
}

// Create instances for different services
// Use Vite proxy paths instead of direct URLs for better compatibility
// predictionClient has 5 minute timeout for long-running backtests
export const predictionClient = new ApiClient('/api/prediction/v1', 300000)
export const fmpClient = new ApiClient('/api/v1')
// NOTE: executionClient removed - execution-service archived (2025-12-28)
