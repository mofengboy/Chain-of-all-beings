<template>
  <div>
    <Markdown :source="body"/>
    <el-table :data="tableData" style="width: 100%">
      <el-table-column prop="date" label="Date" width="180"/>
      <el-table-column prop="name" label="Name" width="180"/>
      <el-table-column prop="address" label="Address"/>
    </el-table>
  </div>
</template>

<script>
import {ElTable, ElTableColumn} from "element-plus";

export default {
  name: "BlockOfBeings",
  data() {
    return {
      body: "",
      tableData: [
        {
          date: '2016-05-03',
          name: 'Tom',
          address: 'No. 189, Grove St, Los Angeles',
        },
        {
          date: '2016-05-02',
          name: 'Tom',
          address: 'No. 189, Grove St, Los Angeles',
        },
        {
          date: '2016-05-04',
          name: 'Tom',
          address: 'No. 189, Grove St, Los Angeles',
        },
        {
          date: '2016-05-01',
          name: 'Tom',
          address: 'No. 189, Grove St, Los Angeles',
        },
      ]
    }
  },
  components: {
    ElTable,
    ElTableColumn,
  }
}
</script>

<style scoped>

</style>
