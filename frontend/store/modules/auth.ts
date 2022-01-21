import { VuexModule, Module, Mutation, Action } from 'vuex-module-decorators'
import AuthService from '@/services/AuthService'
import { AuthUser } from '@/types/auth'

@Module({
  name: 'modules/auth',
  stateFactory: true,
  namespaced: true,
})
export default class AuthModule extends VuexModule {
  public status = { loggedIn: false }
  private userProp: AuthUser | null = null

  get user(): AuthUser | null {
    return this.userProp
  }

  get isExpired(): boolean {
    if (!this.userProp) return false
    return this.userProp.isExpired
  }

  get isLoggedIn(): boolean {
    return this.status.loggedIn
  }

  @Mutation
  public loginSuccess(user: AuthUser): void {
    this.userProp = user
    this.status.loggedIn = true
    if (user.idToken) {
      localStorage.setItem('user', JSON.stringify(user))
    }
  }

  @Mutation
  public updateIdToken(idToken: string): void {
    this.userProp!.idToken = idToken
    this.userProp!.isExpired = false
    localStorage.setItem('user', JSON.stringify(this.userProp))
  }

  @Mutation
  public loginFailure(): void {
    this.status.loggedIn = false
    this.userProp = null
    localStorage.removeItem('user')
  }

  @Mutation
  public setExpired(isExpired: boolean): void {
    this.userProp!.isExpired = isExpired
  }

  @Mutation
  public logout(): void {
    this.status.loggedIn = false
    this.userProp = null
    localStorage.removeItem('user')
  }

  @Action
  public checkIsExpired(): Promise<boolean> {
    if (!this.userProp) return Promise.resolve(false)
    if (this.userProp.isExpired) return Promise.resolve(true)
    const payload: any = JSON.parse(atob(this.userProp!.idToken.split('.')[1]!))
    const isExpird = new Date().getTime() > payload.exp * 1000
    this.context.commit('setExpired', isExpird)
    return Promise.resolve(isExpird)
  }

  @Action({ rawError: true })
  public login(data: {
    username: string
    password: string
  }): Promise<AuthUser> {
    return AuthService.login(data.username, data.password).then(
      (user) => {
        this.context.commit('loginSuccess', user)
        return Promise.resolve(user)
      },
      (error) => {
        this.context.commit('loginFailure')
        const message =
          (error.response &&
            error.response.data &&
            error.response.data.message) ||
          error.message ||
          error.toString()
        return Promise.reject(message)
      }
    )
  }

  @Action({ rawError: true })
  refreshToken(): Promise<AuthUser> {
    return AuthService.refreshToken(this.user!.refreshToken).then(
      (userdata) => {
        if (this.user) {
          this.context.commit('updateIdToken', userdata.idToken)
          return Promise.resolve(this.user)
        } else {
          this.context.commit('loginSuccess', userdata)
          return userdata
        }
      },
      (error) => {
        this.context.commit('loginFailure')
        const message =
          (error.response &&
            error.response.data &&
            error.response.data.errorMessage) ||
          error.message ||
          error.toString()
        return Promise.reject(message)
      }
    )
  }

  @Action
  signOut(): void {
    AuthService.logout()
    this.context.commit('logout')
  }
}
