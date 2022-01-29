/* eslint-disable import/no-mutable-exports */
import { Store } from 'vuex'
import { getModule } from 'vuex-module-decorators'
import AuthModule from '@/store/modules/auth'
import DataModule from '@/store/modules/data'
import FileModule from '@/store/modules/file'

let authStore: AuthModule
let dataStore: DataModule
let fileStore: FileModule

function initialiseStores(store: Store<any>): void {
  authStore = getModule(AuthModule, store)
  dataStore = getModule(DataModule, store)
  fileStore = getModule(FileModule, store)
}

export { initialiseStores, authStore, dataStore, fileStore }
