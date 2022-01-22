export interface AuthUser {
  username: string
  token: string
  refreshToken: string
  isExpired: boolean
}
