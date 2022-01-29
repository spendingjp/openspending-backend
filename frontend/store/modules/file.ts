import { VuexModule, Module, Action } from 'vuex-module-decorators'
import FileService from '@/services/FileService'

@Module({
  name: 'modules/file',
  stateFactory: true,
  namespaced: true,
})
class FileModule extends VuexModule {
  @Action({ rawError: true })
  download(): Promise<any> {
    return FileService.getFile().then(
      () => {
        return Promise.resolve()
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
}

export default FileModule
