import { Government } from './government'
import { BudgetTreeNode } from './budget-tree-node'

export interface WdmmgResponse {
  id: string
  name: string
  subtitle: string
  slug: string
  year: number
  createdAt: string
  updatedAt: string
  government: Government
  budgets: BudgetTreeNode[]
}
