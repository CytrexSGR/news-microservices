/**
 * Trading API Client
 *
 * Connects to:
 * - prediction-service (Port 8116): Strategy analysis, signals, ML Lab
 *
 * NOTE: execution-service (Port 8120) removed - service archived (2025-12-28)
 * Trading execution features will be rebuilt as part of prediction-service refactoring.
 */

import axios from 'axios'

// Prediction Service API (Port 8116)
export const predictionApi = axios.create({
  baseURL: import.meta.env.VITE_PREDICTION_API_URL || 'http://localhost:8116/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// NOTE: executionApi and tradingApi removed - execution-service archived (2025-12-28)
// These features will be rebuilt as part of prediction-service refactoring.
