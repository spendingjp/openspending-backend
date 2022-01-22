/* eslint-disable import/no-mutable-exports */
import { Store } from 'vuex'
import { getModule } from 'vuex-module-decorators'
import AuthModule from '@/store/modules/auth'
import DataModule from '@/store/modules/data'

let authStore: AuthModule
let dataStore: DataModule

function initialiseStores(store: Store<any>): void {
  authStore = getModule(AuthModule, store)
  dataStore = getModule(DataModule, store)
}

export { initialiseStores, authStore, dataStore }
