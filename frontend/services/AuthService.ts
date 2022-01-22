import { $axios } from '@/utils/api-accessor'
import { AuthUser } from '@/types/auth'

class AuthService {
  login(username: string, password: string): Promise<AuthUser> {
    return $axios
      .post('/api-token-auth/', {
        username,
        password,
      })
      .then((response) => {
        return { ...response.data, isExpired: false }
      })
  }

  refreshToken(refreshToken: string): Promise<AuthUser> {
    return $axios
      .post('/api-token-auth/', {
        refreshToken,
      })
      .then((response) => {
        return response.data
      })
  }

  logout() {
    localStorage.removeItem('openspending')
  }
}

export default new AuthService()
