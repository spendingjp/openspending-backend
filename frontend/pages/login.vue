<template>
  <v-card width="400px" class="mx-auto mt-5">
    <v-card-title>
      <h1 class="display-1">ログイン</h1>
    </v-card-title>
    <v-card-text>
      <v-form>
        <v-text-field
          v-model="name"
          label="ユーザ名"
          prepend-icon="mdi-account-circle"
        />
        <v-text-field
          v-model="password"
          label="パスワード"
          prepend-icon="mdi-lock"
          :type="showPassword ? 'text' : 'password'"
          :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
          @click:append="showPassword = !showPassword"
        />
        <v-card-actions>
          <v-btn class="info" @click="handleLogin">ログイン</v-btn>
        </v-card-actions>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script>
import Vue from 'vue'
import { authStore } from '@/store'

export default Vue.extend({
  data() {
    return {
      showPassword: false,
      name: '',
      password: '',
    }
  },
  created() {
    if (authStore.user != null) {
      authStore.refreshToken().then(() => {
        this.$router.push('/')
      })
    }
  },
  methods: {
    handleLogin() {
      authStore
        .login({
          username: this.name,
          password: this.password,
        })
        .then(
          () => {
            this.$router.push('/')
          },
          (error) => {
            console.error(error)
          }
        )
    },
  },
})
</script>
