<template>
  <budget-list :budgets="budgetList"></budget-list>
</template>

<script lang="ts">
import Vue from 'vue'
import BudgetList from '@/components/BudgetList.vue'
import { BudgetListResponse } from '@/types/budget-list-response'
import '@nuxtjs/axios'

export default Vue.extend({
  components: {
    BudgetList,
  },
  async asyncData({ $axios }) {
    const budgetResponse = (
      await $axios.get<BudgetListResponse>('/api/v1/budgets/')
    ).data
    return { budgetList: budgetResponse.results }
  },
})
</script>
