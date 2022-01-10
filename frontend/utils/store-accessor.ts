/* eslint-disable import/no-mutable-exports */
import { Store } from 'vuex'
import { getModule } from 'vuex-module-decorators'
import DataModule from '@/store/modules/data'

let dataStore: DataModule

function initialiseStores(store: Store<any>): void {
  dataStore = getModule(DataModule, store)
}

export { initialiseStores, dataStore }
