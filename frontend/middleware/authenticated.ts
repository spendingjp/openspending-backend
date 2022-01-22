import { Middleware } from '@nuxt/types'
import { authStore } from '@/utils/store-accessor'

const authenticated: Middleware = ({ route, redirect }) => {
  if (!authStore.status.loggedIn && route.path !== '/login') {
    redirect('/login')
  }
}

export default authenticated
