<template>
  <v-container>
    <v-row v-if="state.wdmmgTree">
      <wdmmg-tree :wdmmg-tree="state.wdmmgTree"></wdmmg-tree>
    </v-row>
    <v-row v-else justify="center">
      <v-progress-circular
        :size="100"
        :width="10"
        indeterminate
      ></v-progress-circular>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import {
  defineComponent,
  reactive,
  useAsync,
  useRoute,
} from '@nuxtjs/composition-api'
import { $axios } from '@/utils/api-accessor'
import { WdmmgResponse } from '@/types/wdmmg-response'
import WdmmgTree from '@/components/WdmmgTree.vue'

type State = {
  wdmmgTree: WdmmgResponse | null
}
export default defineComponent({
  components: {
    WdmmgTree,
  },
  setup() {
    const state = reactive<State>({
      wdmmgTree: null,
    })
    const route = useRoute()
    useAsync(async () => {
      state.wdmmgTree = (
        await $axios.get<WdmmgResponse>(
          `/api/v1/wdmmg/${route.value.params.slug}/`,
          { timeout: 9999999 }
        )
      ).data
    })
    return { state }
  },
})
</script>
