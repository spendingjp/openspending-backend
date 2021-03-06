import { NuxtAxiosInstance } from '@nuxtjs/axios' // eslint-disable-line import/named

// eslint-disable-next-line import/no-mutable-exports
let $axios: NuxtAxiosInstance

export function initializeAxios(axiosInstance: NuxtAxiosInstance): void {
  $axios = axiosInstance
}

export { $axios }
