export interface BudgetTreeNode {
  id: string
  name: string
  code: string
  amount: number
  children: BudgetTreeNode[] | null
}
