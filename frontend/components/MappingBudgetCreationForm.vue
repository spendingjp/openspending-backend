<template>
  <v-row justify="center">
    <v-dialog v-model="state.dialog" max-width="600px">
      <template #activator="{ on, attrs }">
        <v-btn v-bind="attrs" v-on="on">
          この予算を元にマッピングを編集/作成
        </v-btn>
      </template>
      <v-card>
        <v-tabs v-model="state.tab" centered dark icons-and-text>
          <v-tabs-slider></v-tabs-slider>
          <v-tab>編集<v-icon>mdi-pencil</v-icon></v-tab>
          <v-tab>新規作成<v-icon>mdi-plus</v-icon></v-tab>
          <v-tabs-items v-model="state.tab">
            <v-tab-item>
              <v-card-title>編集する予算を選択</v-card-title>
              <v-card-text>
                <v-container>
                  <v-row>
                    <v-autocomplete
                      v-model="state.selectedMappedBudgetSlug"
                      :items="relatedBudgets"
                      item-text="name"
                      item-value="slug"
                      label="編集する予算"
                    ></v-autocomplete>
                  </v-row>
                </v-container>
              </v-card-text>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn @click="state.dialog = false"> キャンセル </v-btn>
                <v-btn
                  :to="`/budgets/${state.selectedMappedBudgetSlug}/mapping`"
                  :disabled="state.selectedMappedBudgetSlug === null"
                  nuxt
                  >編集</v-btn
                >
              </v-card-actions>
            </v-tab-item>
            <v-tab-item>
              <v-card-title>マッピング先の予算を選択 </v-card-title>
              <v-card-text>
                <v-container>
                  <v-row>
                    <v-text-field
                      v-model="state.newBudgetName"
                      label="予算名"
                      required
                    ></v-text-field>
                  </v-row>
                  <v-row>
                    <v-autocomplete
                      v-model="state.selectedClassificationSystemIdForNewBudget"
                      :items="mappedBudgetCandidate"
                      item-text="name"
                      item-value="id"
                      label="マッピング先の予算体系"
                    ></v-autocomplete>
                  </v-row>
                </v-container>
              </v-card-text>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn @click="state.dialog = false"> キャンセル </v-btn>
                <v-btn
                  :disabled="
                    state.selectedClassificationSystemIdForNewBudget === null ||
                    state.newBudgetName === ''
                  "
                  @click="handleCreateNewBudget"
                  >新規作成</v-btn
                >
              </v-card-actions>
            </v-tab-item>
            <v-tab-item>tab2</v-tab-item>
          </v-tabs-items>
        </v-tabs>
      </v-card>
    </v-dialog>
  </v-row>
</template>

<script lang="ts">
import { defineComponent, reactive } from '@vue/composition-api'
import { useAsync, SetupContext, useRouter } from '@nuxtjs/composition-api'
import authHeader from '@/services/auth-header'
import { $axios } from '@/utils/api-accessor'
import { ClassificationSystemListItem } from '@/types/classification-system-list-item'
import { Budget } from '@/types/budget'

type State = {
  dialog: Boolean
  selectedMappedBudgetSlug: string | null
  newBudgetName: string
  selectedClassificationSystemIdForNewBudget: string | null
}

export default defineComponent({
  components: {},
  props: {
    currentBudgetId: {
      type: String,
      default: '',
      required: true,
    },
    mappedBudgetCandidate: {
      type: Array as () => ClassificationSystemListItem[],
      default: () => [],
    },
    relatedBudgets: {
      type: Array as () => Budget[],
      default: () => [],
    },
  },
  setup({ currentBudgetId }, ctx: SetupContext) {
    const state = reactive<State>({
      dialog: false,
      selectedMappedBudgetSlug: null,
      newBudgetName: '',
      selectedClassificationSystemIdForNewBudget: null,
    })
    const router = useRouter()
    const handleCreateNewBudget = (): void => {
      useAsync(async () => {
        try {
          const res = (
            await $axios.post<Budget>(
              '/api/v1/budgets/',
              {
                sourceBudget: currentBudgetId,
                classificationSystem:
                  state.selectedClassificationSystemIdForNewBudget,
                name: state.newBudgetName,
              },
              {
                headers: authHeader(),
              }
            )
          ).data
          router.push(`/budgets/${res.slug}/mapping/`)
        } catch (error) {
          ctx.emit('error', '新規予算作成に失敗しました')
        }
      })
    }
    return { state, handleCreateNewBudget }
  },
})
</script>
