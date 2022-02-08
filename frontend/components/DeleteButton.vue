<template>
  <v-btn :loading="loading" :disabled="loading" @click="handleClick"
    >削除</v-btn
  >
</template>

<script lang="ts">
import { defineComponent, SetupContext } from '@vue/composition-api'

export default defineComponent({
  props: {
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  setup(_, context: SetupContext) {
    const handleClick = (): void => {
      context.emit('delete')
    }
    return { handleClick }
  },
})
</script>
