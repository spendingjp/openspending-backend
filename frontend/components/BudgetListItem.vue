<template>
  <v-list-item :href="`table/${budget.id}`">
    <v-list-item-content>
      <v-list-item-title
        v-text="`${budget.name} (${budget.year})`"
      ></v-list-item-title>
      <v-list-item-subtitle
        v-text="`${budget.subtitle} ${budget.updatedAt}`"
      ></v-list-item-subtitle>
    </v-list-item-content>
  </v-list-item>
</template>

<script lang="ts">
import { defineComponent } from '@vue/composition-api'
import { Budget } from '@/types/budget'

export default defineComponent({
  props: {
    budget: {
      type: Object as () => Budget,
      required: true,
    },
  },
  setup({ budget }) {
    return budget
  },
})
</script>
