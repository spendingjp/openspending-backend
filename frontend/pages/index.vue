<template>
  <v-container>
    <v-row>
      <government-selector
        v-model="state.selectedGovernment"
        :government-list="state.governmentList"
        @input="handleSelectGovernment"
      ></government-selector>
    </v-row>
    <v-row>
      <budget-list
        :budgets="state.budgetList"
        @delete-budget="handleDeleteBudget"
      ></budget-list>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import { defineComponent, reactive, useAsync } from '@nuxtjs/composition-api'
import GovernmentSelector from '../components/GovernmentSelector.vue'
import { $axios } from '@/utils/api-accessor'
import BudgetList from '@/components/BudgetList.vue'
import { Budget } from '@/types/budget'
import { Government } from '@/types/government'
import { BudgetListResponse } from '@/types/budget-list-response'
import { GovernmentListResponse } from '@/types/government-list-response'

type State = {
  budgetList: Budget[]
  governmentList: Government[]
  selectedGovernmentId: String | null
}
export default defineComponent({
  components: {
    BudgetList,
    GovernmentSelector,
  },
  setup() {
    const state = reactive<State>({
      budgetList: [],
      governmentList: [],
      selectedGovernmentId: null,
    })
    useAsync(async () => {
      state.governmentList = (
        await $axios.get<GovernmentListResponse>('/api/v1/governments/')
      ).data.results
      state.budgetList = reactive<Budget[]>(
        (await $axios.get<BudgetListResponse>('/api/v1/budgets/')).data.results
      )
    })
    const handleDeleteBudget = (e: number): void => {
      state.budgetList.splice(e, 1)
    }
    const handleSelectGovernment = (e: string | null): void => {
      state.selectedGovernmentId = e
      useAsync(async () => {
        state.budgetList = reactive<Budget[]>(
          (
            await $axios.get<BudgetListResponse>(
              `/api/v1/budgets/${
                state.selectedGovernmentId !== null
                  ? '?government=' + state.selectedGovernmentId
                  : ''
              }`
            )
          ).data.results
        )
      })
    }
    return { state, handleDeleteBudget, handleSelectGovernment }
  },
})
</script>
