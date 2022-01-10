/* eslint-disable import/no-mutable-exports */
import { Store } from 'vuex'
import { getModule } from 'vuex-module-decorators'
import DataModule from '@/store/modules/data'
import AuthModule from '@/store/modules/auth'

let dataStore: DataModule
let authStore: AuthModule

function initialiseStores(store: Store<any>): void {
  dataStore = getModule(DataModule, store)
  authStore = getModule(AuthModule, store)
}

export { initialiseStores, dataStore, authStore }
