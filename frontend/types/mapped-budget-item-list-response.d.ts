import { MappedBudgetItem } from './mapped-budget-item'

export interface MappedBudgetItemListResponse {
  next: string | null
  prev: string | null
  results: MappedBudgetItem[]
}
