<template>
  <div>
    <v-treeview :items="wdmmgTree" transition open-on-click>
      <template #label="{ item }">
        {{ `${item.code}. ${item.name}: ${item.amount}` }}
      </template>
      <template #append="{ item }">
        <div @click.stop>
          <v-autocomplete
            :value="item.targetClassification"
            :items="classifications"
            item-value="id"
            dense
            @change="(e) => handleChange(item)(e)"
          >
            <template #item="{ item: targetClassification }">
              {{ `${targetClassification.code} ${targetClassification.name}` }}
            </template>
            <template #selection="{ item: targetClassification }">
              {{ `${targetClassification.code} ${targetClassification.name}` }}
            </template>
          </v-autocomplete>
        </div>
      </template>
    </v-treeview>
  </div>
</template>

<script lang="ts">
import { defineComponent } from '@vue/composition-api'
import { SetupContext } from '@nuxtjs/composition-api'
import { Classification } from '~/types/classification'
import { ParentAwareBudgetTreeNode } from '@/types/parent-aware-budget-tree-node'

export default defineComponent({
  props: {
    wdmmgTree: {
      type: Array as () => ParentAwareBudgetTreeNode[],
      required: true,
    },
    classifications: {
      type: Array as () => Classification[],
      required: true,
    },
  },
  setup(_, ctx: SetupContext) {
    const handleChange = (item: ParentAwareBudgetTreeNode) => {
      return (e: string): void => {
        ctx.emit('change', [item, e])
      }
    }
    return { handleChange }
  },
})
</script>
