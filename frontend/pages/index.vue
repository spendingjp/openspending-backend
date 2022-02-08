<template>
  <budget-list
    :budgets="state.budgetList"
    @delete-budget="handleDeleteBudget"
  ></budget-list>
</template>

<script lang="ts">
import { defineComponent, reactive, useAsync } from '@nuxtjs/composition-api'
import { $axios } from '@/utils/api-accessor'
import BudgetList from '@/components/BudgetList.vue'
import { Budget } from '@/types/budget'
import { BudgetListResponse } from '@/types/budget-list-response'

type State = {
  budgetList: Budget[]
}
export default defineComponent({
  components: {
    BudgetList,
  },
  setup() {
    const state = reactive<State>({
      budgetList: [],
    })
    useAsync(async () => {
      state.budgetList = reactive<Budget[]>(
        (await $axios.get<BudgetListResponse>('/api/v1/budgets/')).data.results
      )
    })
    const handleDeleteBudget = (e: number): void => {
      state.budgetList.splice(e, 1)
    }
    return { state, handleDeleteBudget }
  },
})
</script>
