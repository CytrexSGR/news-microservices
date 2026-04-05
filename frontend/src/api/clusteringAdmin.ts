import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

// Note: VITE_INTELLIGENCE_API_URL should include /api/v1/intelligence suffix
// Paths below are relative to that base (e.g., /clustering/status not /api/v1/intelligence/clustering/status)
const intelligenceApi = axios.create({
  baseURL: import.meta.env.VITE_INTELLIGENCE_API_URL || 'http://localhost:8118/api/v1/intelligence',
})

// Request interceptor to add auth token
intelligenceApi.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Types
export interface ClusteringTriggerRequest {
  hours: number
  min_samples: number
  eps: number
}

export interface ClusteringTriggerResponse {
  task_id: string
  status: string
  message: string
  parameters: {
    hours: number
    min_samples: number
    eps: number
  }
}

export interface ClusteringStatusResponse {
  current_config: {
    default_hours: number
    default_min_samples: number
    default_eps: number
    metric: string
    algorithm: string
  }
  last_run: string | null
  scheduled_interval: string
  available_parameters: {
    hours: {
      min: number
      max: number
      default: number
      description: string
    }
    min_samples: {
      min: number
      max: number
      default: number
      description: string
    }
    eps: {
      min: number
      max: number
      default: number
      description: string
    }
  }
}

export interface TaskStatusResponse {
  task_id: string
  status: 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE' | 'RETRY'
  result: any | null
}

// API functions
export const clusteringAdminApi = {
  /**
   * Trigger manual clustering with custom parameters
   */
  async triggerClustering(params: ClusteringTriggerRequest): Promise<ClusteringTriggerResponse> {
    const { data } = await intelligenceApi.post('/clustering/trigger', params)
    return data
  },

  /**
   * Get current clustering configuration and status
   */
  async getClusteringStatus(): Promise<ClusteringStatusResponse> {
    const { data } = await intelligenceApi.get('/clustering/status')
    return data
  },

  /**
   * Get status of a clustering task
   */
  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const { data } = await intelligenceApi.get(`/clustering/task/${taskId}`)
    return data
  },
}

export { intelligenceApi }
