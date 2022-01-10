import { VuexModule, Module, Mutation, Action } from 'vuex-module-decorators'
import { ConsumeMap } from '@/types/component-interfaces/data'

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
