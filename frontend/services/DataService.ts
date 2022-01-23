// @ts-ignore
import authHeader from './auth-header'
import { $axios } from '@/utils/api-accessor'
import { ConsumeData, RegisteredData } from '@/types/component-interfaces/data'

class DataService {
  async postData(target: ConsumeData): Promise<RegisteredData[]> {
    const response = await $axios.post(
      '/api/v1/classifiaction-systems/',
      target,
      {
        headers: authHeader(),
      }
    )
    return response.data
  }
}

export default new DataService()
