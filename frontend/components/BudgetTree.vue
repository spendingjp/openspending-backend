<template>
  <v-treeview
    :items="wdmmgTree.budgets"
    selection-type="leaf"
    transition
    open-on-click
    dense
  >
    <template #label="{ item, leaf, selected, indeterminate, active, open }">
      <slot
        name="label"
        :item="item"
        :leaf="leaf"
        :selected="selected"
        :indeterminate="indeterminate"
        :active="active"
        :open="open"
      >
        {{ `${item.code}. ${item.name}: ${item.amount}` }}
      </slot>
    </template>
    <template #append="{ item, leaf, selected, indeterminate, active, open }">
      <slot
        name="append"
        :item="item"
        :leaf="leaf"
        :selected="selected"
        :indeterminate="indeterminate"
        :active="active"
        :open="open"
      >
      </slot>
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
  setup() {},
})
</script>
