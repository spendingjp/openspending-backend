<template>
  <v-list>
    <budget-list-item v-for="b in budgets" :key="b.id" :budget="b">
    </budget-list-item>
  </v-list>
</template>

<script lang="ts">
import { defineComponent } from '@vue/composition-api'
import BudgetListItem from './BudgetListItem.vue'
import { Budget } from '@/types/budget'

export default defineComponent({
  components: { BudgetListItem },
  props: {
    budgets: {
      type: Array as () => Budget[],
      required: true,
    },
  },
  setup({ budgets }) {
    return budgets
  },
})
</script>
