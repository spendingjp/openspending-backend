<template>
  <div>
    <v-data-table
      :headers="headers"
      :footer-props="footerProps"
      :items="originalItems"
      class="elevation-1"
      dense
    >
      <template v-slot:item.cofogLevel1="{ item }">
        <v-select
          v-model="item.cofogLevel1"
          :items="cofogItems"
          item-value="id"
          item-text="text"
          label="COFOG Level1"
          dense
          outlined
          class="mt-4"
          :success="item.cofogLevel1 !== item.copyCofogLevel1"
          :error="!item.cofogLevel1"
          @change="setSelectItemsCofogLevel2(item)"
        ></v-select>
      </template>
      <template v-slot:item.cofogLevel2="{ item }">
        <v-select
          v-model="item.cofogLevel2"
          :items="cofogLevel2Items[item.number]"
          item-value="id"
          item-text="text"
          label="COFOG Level2"
          dense
          outlined
          class="mt-4"
          :success="item.cofogLevel2 !== item.copyCofogLevel2"
          :error="!item.cofogLevel2"
          @change="setSelectItemsCofogLevel3(item)"
        ></v-select>
      </template>
      <template v-slot:item.cofogLevel3="{ item }">
        <v-select
          v-model="item.cofogLevel3"
          :items="cofogLevel3Items[item.number]"
          item-value="id"
          item-text="text"
          label="COFOG Level3"
          dense
          outlined
          class="mt-4"
          append-outer-icon="mdi-cached"
          :success="item.cofogLevel3 !== item.copyCofogLevel3"
          :error="!item.cofogLevel3"
          @click:append-outer="restoreSelect(item)"
          @change="registerMappingArray(item)"
        ></v-select>
      </template>
      <template v-slot:no-data>
        <v-skeleton-loader
          class="mx-auto"
          width="1000"
          type="table"
        ></v-skeleton-loader>
      </template>
    </v-data-table>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import cofog from '@/data/cofog_flatten.json'
import data from '@/data/tsukuba_flatten.json'
import mapping from '@/data/mapping.json'
import { Data, Cofog, Map } from '@/types/component-interfaces/data'
import { dataStore } from '@/store'

interface CofogItem {
  id: string
  text: string
}

interface Action {
  number: number
  cofogLevel1: string | undefined
  cofogLevel2: string | undefined
  cofogLevel3: string | undefined
  copyCofogLevel1: string | undefined
  copyCofogLevel2: string | undefined
  copyCofogLevel3: string | undefined
}

type DataItem = Data & Action

export default Vue.extend({
  data() {
    return {
      headers: [
        { text: 'level1Code', value: 'level1Code', sortable: false },
        { text: 'level1Name', value: 'level1Name', sortable: false, cellClass: 'text-no-wrap' },
        { text: 'level2Code', value: 'level2Code', sortable: false },
        { text: 'level2Name', value: 'level2Name', sortable: false, cellClass: 'text-no-wrap' },
        { text: 'level3Code', value: 'level3Code', sortable: false },
        { text: 'level3Name', value: 'level3Name', sortable: false, cellClass: 'text-no-wrap' },
        { text: 'level4Code', value: 'level4Code', sortable: false },
        { text: 'level4Name', value: 'level4Name', sortable: false, cellClass: 'text-no-wrap' },
        { text: 'level5Code', value: 'level5Code', sortable: false },
        { text: 'level5Name', value: 'level5Name', sortable: false, cellClass: 'text-no-wrap' },
        { text: 'level6Code', value: 'level6Code', sortable: false },
        { text: 'level6Name', value: 'level6Name', sortable: false, cellClass: 'text-no-wrap' },
        { text: 'cofogLevel1', value: 'cofogLevel1', sortable: false },
        { text: 'cofogLevel2', value: 'cofogLevel2', sortable: false },
        { text: 'cofogLevel3', value: 'cofogLevel3', sortable: false },
      ],
      footerProps: {
        itemsPerPageOptions: [50, 100, 150, 200, -1]
      },
      originalData: [] as Data[],
      originalItems: [] as DataItem[],
      mappingData: [] as Map[],
      cofogData: [] as Cofog[],
      cofogItems: [] as CofogItem[],
      cofogLevel2Items: [] as CofogItem[][],
      cofogLevel3Items: [] as CofogItem[][],
    }
  },
  mounted() {
    this.cofogData = cofog.data
    this.cofogItems = this.cofogData.map((item: Cofog) => {
      return {
        id: item.cofogLevel1Id,
        text: `${item.cofogLevel1Code} ${item.cofogLevel1Name}`
      }
    })
    this.mappingData = mapping.data
    this.originalData = data.data
    this.originalItems = this.originalData.map((item, index) => {
      const matchedCofog = this.getMatchCofog(item)
      this.cofogLevel2Items[index] = this.cofogData.filter((v: Cofog) => {
        return v.cofogLevel1Id === matchedCofog?.cofogLevel1Id
      })
        .map((item2: Cofog) => {
          return {
            id: item2.cofogLevel2Id,
            text: `${item2.cofogLevel2Code} ${item2.cofogLevel2Name}`
          }
        })
      this.cofogLevel3Items[index] = this.cofogData.filter((v: Cofog) => {
        return v.cofogLevel2Id === matchedCofog?.cofogLevel2Id
      })
        .map((item3: Cofog) => {
          return {
            id: item3.cofogLevel3Id,
            text: `${item3.cofogLevel3Code} ${item3.cofogLevel3Name}`
          }
        })
      return {
        number: index,
        cofogLevel1: matchedCofog?.cofogLevel1Id,
        cofogLevel2: matchedCofog?.cofogLevel2Id,
        cofogLevel3: matchedCofog?.cofogLevel3Id,
        copyCofogLevel1: JSON.parse(JSON.stringify(matchedCofog?.cofogLevel1Id || '')),
        copyCofogLevel2: JSON.parse(JSON.stringify(matchedCofog?.cofogLevel2Id || '')),
        copyCofogLevel3: JSON.parse(JSON.stringify(matchedCofog?.cofogLevel3Id || '')),
        ...item,
      }
    })
  },
  methods: {
    setSelectItemsCofogLevel2(item: DataItem) {
      this.cofogLevel2Items[item.number] = this.cofogData.filter((v: Cofog) => {
        return v.cofogLevel1Id === item.cofogLevel1
      })
        .map((item: Cofog) => {
          return {
            id: item.cofogLevel2Id,
            text: `${item.cofogLevel2Code} ${item.cofogLevel2Name}`
          }
        })
    },
    setSelectItemsCofogLevel3(item: DataItem) {
      this.cofogLevel3Items[item.number] = this.cofogData.filter((v: Cofog) => {
        return v.cofogLevel2Id === item.cofogLevel2
      })
        .map((item: Cofog) => {
          return {
            id: item.cofogLevel3Id,
            text: `${item.cofogLevel3Code} ${item.cofogLevel3Name}`
          }
        })
    },
    getMatchCofog(item: Data): Cofog | undefined {
      const matched: Map | undefined = this.mappingData.find((v: Map) => { return v.sourceId === item.level6Id })
      const matchedId = matched?.targetId || null
      return this.cofogData.find((v: Cofog) => {
        return v.cofogLevel3Id === matchedId
      })
    },
    restoreSelect(item: DataItem) {
      const restoreItem = Object.assign(item, {
        cofogLevel1: item.copyCofogLevel1,
        cofogLevel2: item.copyCofogLevel2,
        cofogLevel3: item.copyCofogLevel3,
      })
      this.setSelectItemsCofogLevel2(restoreItem)
      this.setSelectItemsCofogLevel3(restoreItem)
      dataStore.removeMap(item.level6Id)
    },
    registerMappingArray(item: DataItem) {
      if (item.cofogLevel3 && item.cofogLevel3 !== item.copyCofogLevel3) {
        dataStore.setMap({ sourceId: item.level6Id, targetId: item.cofogLevel3 })
      }
    },
  }
})
</script>
