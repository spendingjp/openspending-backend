import { VuexModule, Module, Mutation, Action } from 'vuex-module-decorators'
import DataService from '@/services/DataService'
import {
  ConsumeMap,
  ConsumeData,
  RegisteredData,
} from '@/types/component-interfaces/data'

@Module({
  name: 'modules/data',
  stateFactory: true,
  namespaced: true,
})
class DataModule extends VuexModule {
  private newMappingData: ConsumeMap[] = []

  @Mutation
  public setMappingArray(map: ConsumeMap): void {
    this.newMappingData = [...this.newMappingData, map]
  }

  @Mutation
  public removeMappingData(sourseId: string): void {
    this.newMappingData.splice(
      this.newMappingData.findIndex((item) => item.sourceId === sourseId),
      1
    )
  }

  @Action({ rawError: true })
  create(target: ConsumeData): Promise<RegisteredData[]> {
    return DataService.postData(target).then(
      (data) => {
        return Promise.resolve(data)
      },
      (error) => {
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
  setMap(map: ConsumeMap): void {
    this.context.commit('setMappingArray', map)
  }

  @Action
  removeMap(sourceId: string): void {
    this.context.commit('removeMappingData', sourceId)
  }
}

export default DataModule
