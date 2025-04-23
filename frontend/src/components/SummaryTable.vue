<template>
    <div class = "summary-table">
      <table>
        <tbody>
          <tr class = "header">
            <th v-for="(header, index) in headers" :key="`header-${index}`">{{ header }}</th>
          </tr>
          <tr v-for="d in data" :key="d.id">
            <td v-for="(header, index) in headers" :key="`header-data-${index}`">{{ d[header] }}</td>
          </tr>
        </tbody>
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

<style scoped lang="less">
table {
  border-spacing: 0;
  border: 1px solid #000;
  border-bottom: none;
}
th {
  background-color: #aaa;
  border-right: 1px solid #000;
  border-bottom: 1px solid #000;
}
td {
  border-right: 1px solid #000;
  border-bottom: 1px solid #000;
}
th, td {
  padding: 1em;
}
th:last-child, td:last-child {
  border-right: none;
}
</style>
