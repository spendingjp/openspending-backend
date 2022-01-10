import { Module, VuexModule, Mutation } from 'vuex-module-decorators'

@Module({
  name: 'modules/auth',
  stateFactory: true,
  namespaced: true,
})
export default class AuthModule extends VuexModule {
  private token: string = ''
  private name: string = ''

  @Mutation
  public setName(name: string) {
    this.name = name
  }

  public get getName() {
    return this.name
  }

  @Mutation
  public setToken(token: string) {
    this.token = token
  }

  public get getToken() {
    return this.token
  }
}
