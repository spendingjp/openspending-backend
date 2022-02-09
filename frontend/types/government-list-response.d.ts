import { Government } from './government'

export interface GovernmentListResponse {
  next: string
  prev: string
  results: Government[]
}
