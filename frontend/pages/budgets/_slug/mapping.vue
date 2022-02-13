<template>
  <v-container>
    <v-row class="mb-4">
      <h1>COFOG 分類紐付け</h1>
    </v-row>
    <v-row class="mb-8">
      <div>COFOG への紐付けを選択して [反映] をクリックします</div>
    </v-row>
    <v-row v-if="state.wdmmgTree">
      <wdmmg-tree
        :wdmmg-tree="state.wdmmgTree"
        :cofog-classifications="state.cofogClassifications"
      ></wdmmg-tree>
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
import { ClassifiactionSystemResponse } from '@/types/classification-system-response.d.ts'
import WdmmgTree from '@/components/WdmmgTree.vue'
import { Classification } from '~/types/classification'

type State = {
  wdmmgTree: WdmmgResponse | null
  cofogClassifications: Classification[]
}
export default defineComponent({
  components: {
    WdmmgTree,
  },
  setup() {
    const state = reactive<State>({
      wdmmgTree: null,
      cofogClassifications: [],
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
    useAsync(async () => {
      state.cofogClassifications = (
        await $axios.get<ClassifiactionSystemResponse>(
          `/api/v1/classification-systems/cofog/`
        )
      ).data.items
    })
    return { state }
  },
})
</script>
