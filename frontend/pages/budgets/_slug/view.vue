<template>
  <v-container>
    <v-row v-if="state.wdmmgTree" no-gutters>
      <v-col cols="12" sm="12">
        <v-card>
          <v-card-title class="text-h3">{{
            state.wdmmgTree.name
          }}</v-card-title>
          <v-card-subtitle class="text-h6"
            ><v-row
              >{{ state.wdmmgTree.subtitle }}<v-spacer></v-spacer>
              {{ state.wdmmgTree.government.name }} /
              {{ state.wdmmgTree.year }}年 / 最終更新:
              {{ state.wdmmgTree.updatedAt }}</v-row
            >
            <v-row v-if="state.wdmmgTree.sourceBudget !== undefined"
              ><v-spacer></v-spacer>元にした予算:
              <nuxt-link
                :to="`/budgets/${state.wdmmgTree.sourceBudget.slug}/view`"
                >{{ state.wdmmgTree.sourceBudget.name }}</nuxt-link
              ></v-row
            >
            <v-row v-else>
              <mapping-budget-creation-form
                :mapped-budget-candidate="state.mappedBudgetCandidate"
                :related-budgets="state.relatedBudgets"
                :current-budget-id="state.wdmmgTree.id"
                @error="handleError"
              ></mapping-budget-creation-form>
            </v-row>
          </v-card-subtitle>
          <v-divider></v-divider>
          <v-card-text class="text-body-1">
            <v-row>
              <budget-tree :wdmmg-tree="state.wdmmgTree"></budget-tree></v-row
          ></v-card-text>
          <v-card-actions> </v-card-actions>
        </v-card>
      </v-col>
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
  SetupContext,
} from '@nuxtjs/composition-api'
import { $axios } from '@/utils/api-accessor'
import { WdmmgResponse } from '@/types/wdmmg-response'
import { ClassificationSystemListItem } from '@/types/classification-system-list-item'
import { ClassificationSystemListResponse } from '@/types/classification-system-list-response'
import { Budget } from '@/types/budget'
import MappingBudgetCreationForm from '@/components/MappingBudgetCreationForm.vue'
import BudgetTree from '@/components/BudgetTree.vue'

type State = {
  wdmmgTree: WdmmgResponse | null
  mappedBudgetCandidate: ClassificationSystemListItem[]
  relatedBudgets: Budget[]
  mappingBudgetId: string | null
}
export default defineComponent({
  components: {
    BudgetTree,
    MappingBudgetCreationForm,
  },
  setup(_, ctx: SetupContext) {
    const state = reactive<State>({
      wdmmgTree: null,
      mappedBudgetCandidate: [],
      relatedBudgets: [],
      mappingBudgetId: null,
    })
    const route = useRoute()
    useAsync(async () => {
      state.wdmmgTree = (
        await $axios.get<WdmmgResponse>(
          `/api/v1/wdmmg/${route.value.params.slug}/`,
          { timeout: 9999999 }
        )
      ).data
      if (state.wdmmgTree.sourceBudget === undefined) {
        state.mappedBudgetCandidate = (
          await $axios.get<ClassificationSystemListResponse>(
            `/api/v1/budgets/${state.wdmmgTree.id}/mapped-budget-candidates/`
          )
        ).data.results
        state.relatedBudgets = (
          await $axios.get<ClassificationSystemListResponse>(
            `/api/v1/budgets/?sourceBudget=${state.wdmmgTree.id}`
          )
        ).data.results
      }
    })
    const handleError = (e: Event): void => {
      ctx.emit('error', e)
    }
    return { state, handleError }
  },
})
</script>
