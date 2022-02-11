<template>
  <v-list>
    <budget-list-item
      v-for="b in budgets"
      :key="b.id"
      :budget="b"
      @delete-budget="handleDeleteBudget"
    >
    </budget-list-item>
    <div v-if="isBudgetEmpty">{{ commentForEmpty }}</div>
  </v-list>
</template>

<script lang="ts">
import { defineComponent, SetupContext } from '@vue/composition-api'
import { computed, toRefs } from '@nuxtjs/composition-api'
import BudgetListItem from './BudgetListItem.vue'
import { Budget } from '@/types/budget'

export default defineComponent({
  components: { BudgetListItem },
  props: {
    budgets: {
      type: Array as () => Budget[],
      required: true,
    },
    commentForEmpty: {
      type: String,
      required: true,
    },
  },
  setup(props, context: SetupContext) {
    const { budgets } = toRefs(props)

    const handleDeleteBudget = (e: string): void => {
      context.emit('delete-budget', budgets.value.map((d) => d.id).indexOf(e))
    }

    const isBudgetEmpty = computed((): boolean => {
      return budgets.value.length === 0
    })

    return { handleDeleteBudget, isBudgetEmpty }
  },
})
</script>
