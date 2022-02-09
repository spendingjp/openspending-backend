<template>
  <v-list-item>
    <v-list-item-content>
      <v-list-item-title
        v-text="`${budget.name} (${budget.year})`"
      ></v-list-item-title>
      <v-list-item-subtitle
        v-text="`${budget.subtitle} ${budget.updatedAt}`"
      ></v-list-item-subtitle>
    </v-list-item-content>
    <v-list-item-action>
      <v-row>
        <show-button @show="handleShow"></show-button>
        <delete-button :deleting="false" @delete="handleDelete"></delete-button>
      </v-row>
    </v-list-item-action>
  </v-list-item>
</template>

<script lang="ts">
import { defineComponent, SetupContext, ref } from '@vue/composition-api'
import { useRouter } from '@nuxtjs/composition-api'
import DeleteButton from './DeleteButton.vue'
import ShowButton from './ShowButton.vue'
import { $axios } from '@/utils/api-accessor'
import authHeader from '@/services/auth-header'
import { Budget } from '@/types/budget'

export default defineComponent({
  components: { DeleteButton, ShowButton },
  props: {
    budget: {
      type: Object as () => Budget,
      required: true,
    },
  },
  setup({ budget }, context: SetupContext) {
    const router = useRouter()
    const deleting = ref<Boolean>(false)
    const handleDelete = (): void => {
      deleting.value = true
      $axios
        .delete(`/api/v1/budgets/${budget.id}/`, {
          headers: authHeader(),
        })
        .then(() => {
          deleting.value = false
          context.emit('delete-budget', budget.id)
        })
    }
    const handleShow = (): void => {
      router.push(`/table/${budget.slug}`)
    }
    return { deleting, handleDelete, handleShow }
  },
})
</script>
