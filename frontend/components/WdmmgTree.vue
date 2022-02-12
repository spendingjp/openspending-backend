<template>
  <v-treeview
    :items="wdmmgTree.budgets"
    transition
    dense
    selectable
    open-on-click
  >
    <template #label="{ item }">
      {{ `${item.code}. ${item.name}: ${item.amount}` }}
    </template>
  </v-treeview>
</template>

<script lang="ts">
import { defineComponent } from '@vue/composition-api'
import { WdmmgResponse } from '@/types/wdmmg-response'

export default defineComponent({
  props: {
    wdmmgTree: {
      type: Object as () => WdmmgResponse,
      required: true,
    },
  },
  setup() {
    return {}
  },
})
</script>
