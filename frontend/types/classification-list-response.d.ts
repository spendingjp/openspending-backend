import { Classification } from './classification'

export interface ClassificationListResponse {
  next: string | null
  prev: string | null
  results: Classification[]
}
