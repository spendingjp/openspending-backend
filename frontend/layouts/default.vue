<template>
  <v-app>
    <v-app-bar fixed app>
      <back-button @back="handleBack"></back-button>
      <v-toolbar-title v-text="title" />
      <v-spacer />
      <v-btn
        class="mr-4"
        outlined
        :href="`${$config.apiUrl}/transfer/xlsx_template`"
      >
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
import BackButton from '../components/BackButton.vue'
import { authStore } from '@/store'

export default Vue.extend({
  components: { BackButton },
  middleware: ['authenticated'],
  data() {
    return {
      title: 'Where Does My Money Go?',
    }
  },
  methods: {
    handleLogout() {
      authStore.signOut()
      this.$router.push('/login')
    },
    handleBack() {
      this.$router.back()
    },
  },
})
</script>
