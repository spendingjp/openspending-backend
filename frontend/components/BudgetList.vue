<template>
  <v-list>
    <budget-list-item
      v-for="b in budgets"
      :key="b.id"
      :budget="b"
      @delete-budget="handleDeleteBudget"
    >
    </budget-list-item>
  </v-list>
</template>

<script lang="ts">
import { defineComponent, SetupContext } from '@vue/composition-api'
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
  setup({ budgets }, context: SetupContext) {
    const handleDeleteBudget = (e: string): void => {
      context.emit('delete-budget', budgets.map((d) => d.id).indexOf(e))
    }
    return { handleDeleteBudget }
  },
})
</script>
