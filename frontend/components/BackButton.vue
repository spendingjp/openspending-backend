<template>
  <v-btn :disabled="disabled" @click="handleClick">
    <v-icon dark> mdi-arrow-left </v-icon>
  </v-btn>
</template>

<script lang="ts">
import { defineComponent, SetupContext } from '@vue/composition-api'

export default defineComponent({
  props: {
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  setup(_, context: SetupContext) {
    const handleClick = (): void => {
      context.emit('back')
    }
    return { handleClick }
  },
})
</script>
