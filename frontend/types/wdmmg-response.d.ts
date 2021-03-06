import { Government } from './government'
import { Budget } from './budget'
import { BudgetTreeNode } from './budget-tree-node'

export interface WdmmgResponse {
  id: string
  name: string
  subtitle: string
  slug: string
  year: number
  createdAt: string
  updatedAt: string
  sourceBudget?: Budget
  government: Government
  budgets: BudgetTreeNode[]
}
