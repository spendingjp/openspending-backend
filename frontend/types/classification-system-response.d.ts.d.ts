import { Classification } from './classification'

export interface ClassifiactionSystemResponse {
  id: string
  name: string
  slug: string
  levelNames: string[]
  items: Classification[]
  createdAt: string
  updatedAt: string
}
