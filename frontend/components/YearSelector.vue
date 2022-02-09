<template>
  <v-text-field
    label="年度で絞り込む"
    min="1900"
    max="3000"
    clearable
    type="number"
    :value="value"
    @change="handleChange"
  ></v-text-field>
</template>

<script lang="ts">
import { defineComponent, SetupContext } from '@vue/composition-api'

export default defineComponent({
  props: {
    value: {
      type: Number,
      default: null,
      required: false,
    },
  },
  setup(_, ctx: SetupContext) {
    const handleChange = (e: string | null) => {
      if (e === null) {
        ctx.emit('input', null)
      }
      const theValue = parseInt(e)
      if (!Number.isNaN(theValue)) {
        ctx.emit('input', theValue)
      }
    }
    return { handleChange }
  },
})
</script>
