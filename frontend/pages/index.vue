<template>
  <v-container>
    <v-row>
      <v-col cols="8">
        <government-selector
          v-model="state.selectedGovernmentId"
          :government-list="state.governmentList"
          @input="handleFilterChange"
          @change="handleFilterChange"
        ></government-selector>
      </v-col>
      <v-col cols="4">
        <year-selector
          v-model="state.selectedYear"
          @input="handleFilterChange"
          @change="handleFilterChange"
        ></year-selector>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <budget-list
          :budgets="state.budgetList"
          comment-for-empty="指定された条件に合致する予算は登録されていません。"
          @delete-budget="handleDeleteBudget"
        ></budget-list>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import {
  computed,
  defineComponent,
  reactive,
  useAsync,
} from '@nuxtjs/composition-api'
import GovernmentSelector from '../components/GovernmentSelector.vue'
import YearSelector from '../components/YearSelector.vue'
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
  selectedYear: Number | null
}
export default defineComponent({
  components: {
    BudgetList,
    GovernmentSelector,
    YearSelector,
  },
  setup() {
    const state = reactive<State>({
      budgetList: [],
      governmentList: [],
      selectedGovernmentId: null,
      selectedYear: null,
    })
    useAsync(async () => {
      state.governmentList = (
        await $axios.get<GovernmentListResponse>('/api/v1/governments/')
      ).data.results
      state.budgetList = reactive<Budget[]>(
        (await $axios.get<BudgetListResponse>('/api/v1/budgets/')).data.results
      )
    })
    const queryParam = computed((): string =>
      state.selectedGovernmentId === null
        ? state.selectedYear === null
          ? ''
          : `?year=${state.selectedYear}`
        : state.selectedYear === null
        ? `?government=${state.selectedGovernmentId}`
        : `?government=${state.selectedGovernmentId}&year=${state.selectedYear}`
    )

    const handleDeleteBudget = (e: number): void => {
      state.budgetList.splice(e, 1)
    }
    const handleFilterChange = (): void => {
      useAsync(async () => {
        state.budgetList = reactive<Budget[]>(
          (
            await $axios.get<BudgetListResponse>(
              `/api/v1/budgets/${queryParam.value}`
            )
          ).data.results
        )
      })
    }
    return { state, handleDeleteBudget, handleFilterChange }
  },
})
</script>
