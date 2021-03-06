<template>
  <div>
    <v-treeview
      :items="wdmmgTree.budgets"
      selection-type="leaf"
      transition
      open-on-click
    >
      <template #label="{ item }">
        {{ `${item.code}. ${item.name}: ${item.amount}` }}
      </template>
      <template #append="{ item }">
        <div class="tree-suffix-container">
          <div class="cofog-selector-container" @click.stop>
            <v-autocomplete
              v-model="state.clsToCofogMap[item.id]"
              :items="state.cofogClassifications"
              item-text="name"
              item-value="id"
              class="cofog-selector"
              dense
              return-object
            >
              <template #item="{ item: cofogItem }">
                {{ `${cofogItem.code} ${cofogItem.name}` }}
              </template>
              <template #selection="{ item: cofogItem }">
                {{ `${cofogItem.code} ${cofogItem.name}` }}
              </template>
            </v-autocomplete>
          </div>
          <div class="cofog-btn-container" @click.stop>
            <v-btn depressed color="primary" @click="onClickCommitBtn(item)"
              >反映</v-btn
            >
          </div>
        </div>
      </template>
    </v-treeview>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive } from '@vue/composition-api'
import { WdmmgResponse } from '@/types/wdmmg-response'
import { BudgetTreeNode } from '~/types/budget-tree-node'
import { Classification } from '~/types/classification'
// import { $axios } from '~/utils/api-accessor'

type IdToBudgetMap = {
  [id: string]: BudgetTreeNode
}

type ClassificationMap = {
  [id: string]: Classification | null
}

type State = {
  cofogClassifications: Classification[]
  clsToCofogMap: ClassificationMap
}

export default defineComponent({
  props: {
    wdmmgTree: {
      type: Object as () => WdmmgResponse,
      required: true,
    },
    cofogClassifications: {
      type: Array as () => Classification[],
      required: true,
    },
  },
  setup({ wdmmgTree, cofogClassifications }) {
    const state = reactive<State>({
      cofogClassifications,
      clsToCofogMap: {},
    })

    const idToBudgetMap: IdToBudgetMap = {}
    const flatBudgets = (
      budget: BudgetTreeNode,
      idToBudgetMap: IdToBudgetMap
    ) => {
      idToBudgetMap[budget.id] = budget
      if (budget.children) {
        budget.children.forEach((child) => {
          flatBudgets(child, idToBudgetMap)
        })
      }
    }
    wdmmgTree.budgets.forEach((budget) => {
      flatBudgets(budget, idToBudgetMap)
    })

    state.clsToCofogMap = Object.fromEntries(
      Object.entries(idToBudgetMap).map(([key, _]) => [
        key,
        {} as Classification,
      ])
    )

    const onClickCommitBtn = (budget: BudgetTreeNode) => {
      // budget.id は classification の id
      const selectedCofog = state.clsToCofogMap[budget.id]
      console.log('call mappedBudget PUT API', budget, selectedCofog)
      // FIXME
      // const res = await $axios.post(`/api/v1/budgets/${budget.id}/items/`, {
      //
      //   "classification": budget.id,
      //   "mappedClassifications": [selectedCofog?.id]
      // })
      // console.log(res)
    }

    return {
      onClickCommitBtn,
      state,
    }
  },
})
</script>

<style lang="scss" scoped>
.cofog-selector-container {
  margin-left: 4px;
}

.cofog-selector {
  padding: 0;
  margin: 0;
  width: 300px;
  font-size: 8px;
}

.tree-suffix-container {
  display: flex;
}

.cofog-btn-container {
  margin-left: 4px;
}
</style>
