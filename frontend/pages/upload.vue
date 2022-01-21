<template>
  <div>
    <v-file-input
      v-model="file"
      accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
      label="File input"
      outlined
    ></v-file-input>
    <v-btn @click="uploadFile"> アップロード </v-btn>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  data() {
    return {
      file: {} as any,
    }
  },
  methods: {
    uploadFile() {
      const formData = new FormData()
      formData.append('file', this.file)
      this.$axios
        .post('/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        .then(function () {
          console.log('SUCCESS!!')
        })
        .catch(function () {
          console.log('FAILURE!!')
        })
    },
  },
})
</script>
