import { Plugin } from '@nuxt/types'
import { initializeAxios } from '@/utils/api-accessor'

export const accessor: Plugin = ({ $axios }): void => {
  const api = $axios.create({
    timeout: 5000,
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFTOKEN',
  })
  initializeAxios(api)
}

export default accessor
