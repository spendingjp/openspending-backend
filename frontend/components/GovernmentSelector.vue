<template>
  <v-autocomplete
    clearable
    label="自治体で絞り込む"
    item-text="name"
    item-value="id"
    :value="value"
    :items="governmentList"
    @change="handleChange"
  ></v-autocomplete>
</template>

<script lang="ts">
import { defineComponent, SetupContext } from '@vue/composition-api'
import { Government } from '@/types/government'

export default defineComponent({
  props: {
    value: {
      type: String as () => string | null,
      required: false,
      default: null,
    },
    governmentList: {
      type: Array as () => Government[],
      required: true,
      default: () => [],
    },
  },
  setup(_, ctx: SetupContext) {
    const handleChange = (e: Event): void => {
      ctx.emit('input', e)
    }
    return { handleChange }
  },
})
</script>
