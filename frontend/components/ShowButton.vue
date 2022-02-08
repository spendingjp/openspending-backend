<template>
  <v-btn @click="handleClick">表示</v-btn>
</template>

<script lang="ts">
import { defineComponent, SetupContext } from '@vue/composition-api'

export default defineComponent({
  props: {},
  setup(_, context: SetupContext) {
    const handleClick = (): void => {
      context.emit('show')
    }
    return { handleClick }
  },
})
</script>
