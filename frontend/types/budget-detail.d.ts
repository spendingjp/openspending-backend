import { Government } from './government'
import { ClassificationSystemListItem } from './classification-system-list-item'

export interface BudgetDetail {
  id: string
  name: string
  slug: string
  year: number
  subtitle: string
  government: Government
  classificationSystem: ClassificationSystemListItem
  sourceBudget?: BudgetDetail
  createdAt: string
  updatedAt: string
}
