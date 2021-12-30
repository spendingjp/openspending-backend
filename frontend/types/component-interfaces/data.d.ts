export interface Data {
  level1Id: string
  level1Code: string
  level1Name: string
  level2Id: string
  level2Code: string
  level2Name: string
  level3Id: string
  level3Code: string
  level3Name: string
  level4Id: string
  level4Code: string
  level4Name: string
  level5Id: string
  level5Code: string
  level5Name: string
  level6Id: string
  level6Code: string
  level6Name: string
  value: number
}

export interface Cofog {
  cofogLevel3Id: string
  cofogLevel3Name: string
  cofogLevel3Code: string
  cofogLevel2Id: string
  cofogLevel2Name: string
  cofogLevel2Code: string
  cofogLevel1Id: string
  cofogLevel1Name: string
  cofogLevel1Code: string
}

export interface Map {
  id: string
  sourceId: string
  targetId: string
}
