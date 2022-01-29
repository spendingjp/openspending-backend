// @ts-ignore
import authHeader from './auth-header'
import { $axios } from '@/utils/api-accessor'

const downloadBlob = (blob: Blob, fileName: string, type: string) => {
  if (window.navigator.msSaveOrOpenBlob) {
    // for IE,Edge
    window.navigator.msSaveOrOpenBlob(blob, fileName)
  } else {
    // for chrome, firefox
    const url = URL.createObjectURL(new Blob([blob], { type }))
    const linkEl = document.createElement('a')
    linkEl.href = url
    linkEl.setAttribute('download', fileName)
    document.body.appendChild(linkEl)
    linkEl.click()

    URL.revokeObjectURL(url)
    linkEl.parentNode?.removeChild(linkEl)
  }
}

const getFileNameFromContentDisposition = (disposition: string) => {
  const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
  const matches = filenameRegex.exec(disposition)
  if (matches != null && matches[1]) {
    const fileName = matches[1].replace(/['"]/g, '')
    return decodeURI(fileName)
  } else {
    return null
  }
}

class FileService {
  async getFile(): Promise<any> {
    const response = await $axios.get('/transfer/xlsx_template', {
      headers: authHeader(),
      responseType: 'blob',
    })
    const disposition = response.headers['content-disposition']
    const fileName = getFileNameFromContentDisposition(disposition) ?? 'file'
    const type = response.headers['content-type']
    downloadBlob(response.data, fileName, type)
  }
}

export default new FileService()
