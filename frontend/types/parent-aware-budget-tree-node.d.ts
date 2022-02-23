import { BudgetTreeNode } from './budget-tree-node'

export interface ParentAwareBudgetTreeNode extends BudgetTreeNode {
  parent: ParentAwareBudgetTreeNode | null
  children: ParentAwareBudgetTreeNode[] | null
  targetClassification: string | null
  originalTargetClassification: string | null
  setTargetClassification(classificationId: string | null): number
  fixTarget(): void
  fixDown(): number
  fixUp(): void
  restoreOriginal(): number
  restoreOriginalDown(): number
  collectSubmitData(query: Map<string, string[]>): void
  moveOriginDown(): void
}
