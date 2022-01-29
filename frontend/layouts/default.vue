<template>
  <v-app>
    <v-app-bar fixed app>
      <v-toolbar-title v-text="title" />
      <v-spacer />
      <v-btn class="mr-4" outlined @click="downloadTemplate">
        テンプレートをダウンロード
      </v-btn>
      <v-btn outlined @click="handleLogout">ログアウト</v-btn>
    </v-app-bar>
    <v-main>
      <v-container>
        <Nuxt />
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
import Vue from 'vue'
import { authStore, fileStore } from '@/store'

export default Vue.extend({
  middleware: ['authenticated'],
  data() {
    return {
      title: 'Vuetify.js',
    }
  },
  methods: {
    downloadTemplate() {
      fileStore.download()
    },
    handleLogout() {
      authStore.signOut()
      this.$router.push('/login')
    },
  },
})
</script>
