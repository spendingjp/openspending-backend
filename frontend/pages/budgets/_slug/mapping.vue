<template>
  <v-container>
    <v-row v-if="state.formData.length > 0">
      <v-col cols="12" sm="12">
        <v-card>
          <v-card-title class="text-h3">{{
            `${state.budget.name} 編集画面`
          }}</v-card-title>
          <v-card-subtitle class="text-h6"
            ><v-row
              ><v-spacer></v-spacer> {{ state.budget.government.name }} /
              {{ state.budget.year }}年 / 最終更新:
              {{ state.budget.updatedAt }}</v-row
            >
            <v-row
              ><v-spacer></v-spacer>元にした予算:
              <nuxt-link
                :to="`/budgets/${state.budget.sourceBudget.slug}/view`"
                >{{ state.budget.sourceBudget.name }}</nuxt-link
              ></v-row
            >
            <v-row>
              <v-spacer></v-spacer>
            </v-row>
          </v-card-subtitle>
          <v-divider></v-divider>
          <v-card-subtitle class="text-h6">
            <v-row>
              <v-spacer></v-spacer>
              <v-btn
                :disabled="state.changedNodeCount === 0"
                @click="handleSubmit"
                >反映</v-btn
              ><v-btn
                :disabled="state.changedNodeCount === 0"
                @click="handleReset"
                >リセット</v-btn
              >
            </v-row>
          </v-card-subtitle>
          <v-divider></v-divider>
          <v-card-text class="text-body-1">
            <budget-mapper-tree
              :wdmmg-tree="state.formData"
              :classifications="state.classifications"
              @change="handleChange"
            ></budget-mapper-tree>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row v-else justify="center">
      <v-progress-circular
        :size="100"
        :width="10"
        indeterminate
      ></v-progress-circular>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import {
  defineComponent,
  reactive,
  useAsync,
  useRoute,
  SetupContext,
} from '@nuxtjs/composition-api'
import { $axios } from '@/utils/api-accessor'
import authHeader from '@/services/auth-header'
import { WdmmgResponse } from '@/types/wdmmg-response'
import { BudgetDetail } from '@/types/budget-detail'
import BudgetMapperTree from '@/components/BudgetMapperTree.vue'
import { Classification } from '@/types/classification'
import { ClassificationListResponse } from '@/types/classification-list-response'
import { MappedBudgetItemListResponse } from '@/types/mapped-budget-item-list-response'
import { BudgetTreeNode } from '@/types/budget-tree-node'
import { ParentAwareBudgetTreeNode } from '@/types/parent-aware-budget-tree-node'

class MappingNodeData implements ParentAwareBudgetTreeNode {
  id: string
  name: string
  code: string
  amount: number
  parent: ParentAwareBudgetTreeNode | null
  children: ParentAwareBudgetTreeNode[] | null
  targetClassification: string | null
  originalTargetClassification: string | null

  constructor(
    node: BudgetTreeNode,
    parent: ParentAwareBudgetTreeNode | null,
    sourceClassificationToTargetClassificationMap: Map<string, string>
  ) {
    this.id = node.id
    this.name = node.name
    this.code = node.code
    this.amount = node.amount
    this.parent = parent
    if (node.children === null) {
      this.children = null
    } else {
      this.children = node.children.map((d) => {
        return new MappingNodeData(
          d,
          this,
          sourceClassificationToTargetClassificationMap
        )
      })
    }
    this.originalTargetClassification =
      sourceClassificationToTargetClassificationMap.get(this.id) || null
    this.targetClassification = this.originalTargetClassification
    this.fixTarget()
  }

  setTargetClassification(classificationId: string | null): number {
    if (this.children === null) {
      if (this.originalTargetClassification === this.targetClassification) {
        if (this.targetClassification !== classificationId) {
          this.targetClassification = classificationId
          return 1
        }
        return 0
      }
      this.targetClassification = classificationId
      return this.originalTargetClassification === this.targetClassification
        ? -1
        : 0
    }
    this.targetClassification = classificationId
    return 0
  }

  fixTarget() {
    if (this.children !== null) {
      const s = new Set<string | null>(
        this.children.map((d) => d.targetClassification)
      )
      if (s.size === 1) {
        this.setTargetClassification(Array.from(s)[0])
      } else {
        this.setTargetClassification(null)
      }
    }
  }

  fixDown(): number {
    let cnt = 0
    if (this.children !== null) {
      this.children.forEach((d) => {
        cnt += d.setTargetClassification(this.targetClassification)
        cnt += d.fixDown()
      })
    }
    return cnt
  }

  fixUp() {
    this.fixTarget()
    if (this.parent !== null) {
      this.parent.fixUp()
    }
  }

  restoreOriginal(): number {
    return this.setTargetClassification(this.originalTargetClassification)
  }

  restoreOriginalDown(): number {
    let cnt = 0
    cnt += this.restoreOriginal()
    if (this.children !== null) {
      this.children.forEach((d) => {
        cnt += d.restoreOriginalDown()
      })
    }
    this.fixTarget()
    return cnt
  }

  collectSubmitData(query: Map<string, string[]>): void {
    if (this.children === null) {
      if (this.targetClassification !== null) {
        if (query.has(this.targetClassification)) {
          query.get(this.targetClassification)!.push(this.id)
        } else {
          query.set(this.targetClassification, [this.id])
        }
      }
    } else {
      this.children.forEach((d) => {
        d.collectSubmitData(query)
      })
    }
  }

  moveOriginDown(): void {
    if (this.children === null) {
      this.originalTargetClassification = this.targetClassification
    } else {
      this.children.forEach((d) => {
        d.moveOriginDown()
      })
      this.fixTarget()
    }
  }
}

type State = {
  budget: BudgetDetail | null
  formData: MappingNodeData[]
  classifications: Classification[]
  changedNodeCount: number
}
export default defineComponent({
  components: {
    BudgetMapperTree,
  },
  setup(_, ctx: SetupContext) {
    const state = reactive<State>({
      budget: null,
      formData: [],
      classifications: [],
      changedNodeCount: 0,
    })

    const route = useRoute()
    const getClassifications = async function (csId: string) {
      let classifications: Classification[] = []
      let next = `/api/v1/classification-systems/${csId}/classifications/`
      while (next !== null) {
        const res = (await $axios.get<ClassificationListResponse>(next)).data
        classifications = classifications.concat(res.results)
        next = res.next!!
      }
      return classifications
    }
    const getMapping = async (
      budgetId: string
    ): Promise<Map<string, string>> => {
      const sourceClassificationIdToTargetClassificationIdMap: Map<
        string,
        string
      > = new Map<string, string>()
      let next = `/api/v1/budgets/${budgetId}/items/`
      while (next !== null) {
        const res = (await $axios.get<MappedBudgetItemListResponse>(next)).data
        res.results.forEach(function (d) {
          d.sourceClassifications.forEach(function (dd) {
            sourceClassificationIdToTargetClassificationIdMap.set(
              dd,
              d.classification
            )
          })
        })
        next = res.next!!
      }
      return sourceClassificationIdToTargetClassificationIdMap
    }
    useAsync(async () => {
      state.budget = (
        await $axios.get<BudgetDetail>(
          `/api/v1/budgets/${route.value.params.slug}/`
        )
      ).data

      state.classifications = await getClassifications(
        state.budget.classificationSystem.id
      )
      const sourceClassificationToTargetClassificationMap = await getMapping(
        state.budget.id
      )
      const wdmmgTree = (
        await $axios.get<WdmmgResponse>(
          `/api/v1/wdmmg/${state.budget.sourceBudget!!.slug}/`,
          { timeout: 9999999 }
        )
      ).data
      state.formData = wdmmgTree.budgets.map(
        (d) =>
          new MappingNodeData(
            d,
            null,
            sourceClassificationToTargetClassificationMap
          )
      )
    })
    const handleChange = (e: [ParentAwareBudgetTreeNode, string]) => {
      state.changedNodeCount += e[0].setTargetClassification(e[1])
      state.changedNodeCount += e[0].fixDown()
      e[0].fixUp()
    }
    const handleReset = (): void => {
      state.formData.forEach((d) => {
        state.changedNodeCount += d.restoreOriginalDown()
      })
    }
    const handleSubmit = (): void => {
      useAsync(async () => {
        const changedNodeCountBackup = state.changedNodeCount
        state.changedNodeCount = 0
        const query = new Map<string, string[]>()
        state.formData.forEach((d) => {
          d.collectSubmitData(query)
        })
        try {
          await $axios.post<any>(
            `/api/v1/budgets/${state.budget!.id}/bulk-create/`,
            {
              data: Array.from(query.entries(), ([key, value]) => {
                return { classification: key, sourceClassifications: value }
              }),
            },
            {
              headers: authHeader(),
            }
          )
          state.formData.forEach((d) => {
            d.moveOriginDown()
          })
          ctx.emit('ok', '予算の更新処理に成功しました')
        } catch (error) {
          state.changedNodeCount = changedNodeCountBackup
          ctx.emit('error', '予算の更新処理に失敗しました')
        }
      })
    }
    return { state, handleChange, handleReset, handleSubmit }
  },
})
</script>
