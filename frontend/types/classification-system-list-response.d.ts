import { ClassificationSystemListItem } from './classification-system-list-item'

export interface ClassificationSystemListResponse {
  next: string
  prev: string
  results: ClassificationSystemListItem[]
}
