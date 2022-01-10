<template>
  <v-app>
    <v-app-bar fixed app>
      <v-toolbar-title v-text="title" />
    </v-app-bar>
    <v-main>
      <v-card width="400px" class="mx-auto mt-5">
        <v-card-title>
          <h1 class="display-1">ログイン</h1>
        </v-card-title>
        <v-card-text>
          <v-form>
            <v-text-field
              v-model="name"
              label="ユーザ名"
              prepend-icon="mdi-account-circle"/>
            <v-text-field
              v-model="password"
              label="パスワード"
              prepend-icon="mdi-lock"
              :type="showPassword ? 'text' : 'password'"
              :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
              @click:append="showPassword = !showPassword"/>
            <v-card-actions>
              <v-btn
                class="info"
                @click="submit">ログイン</v-btn>
            </v-card-actions>
          </v-form>
        </v-card-text>
      </v-card>
      <v-container>
        <Nuxt />
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
export default {
  data() {
    return {
      title: 'Vuetify.js',
      showPassword : false,
      name:'',
      password:'',
    }
  },
  methods: {
    submit() {
      console.log(this.name,this.password)
    }
  },
}
</script>
