import { Budget } from './budget'

export interface BudgetListResponse {
  next: string
  prev: string
  results: Budget[]
}
