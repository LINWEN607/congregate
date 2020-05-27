<template>
    <div class = "summary-table">
      <table>
          <tr class = "header">
            <th v-for="(header, index) in headers" :key="`header-${index}`">{{ header }}</th>
          </tr>
          <tr v-for="d in data" :key="d.id">
            <td v-for="(header, index) in headers" :key="`header-data-${index}`">{{ d[header] }}</td>
          </tr>
        </table>
    </div>
</template>

<script>
export default {
  name: 'SummaryTable',
  props: {
    headers: Array,
    data: Array
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="less">
</style>
