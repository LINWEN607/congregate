<template>
    <table v-if="data.length > 0">
        <tbody>
            <tr>
                <th v-for="header in headers">{{ header }}</th>
            </tr>
            <tr v-for="row in data">
                <td v-for="key in headers">{{ row[key] }}</td>
            </tr>
        </tbody>
    </table>
</template>
<script>
export default {
  name: 'StatusTable',
  components: {},
  props: ['headers', 'data']
}
</script>
<style scoped>
table {
    border: 1px solid #000;
    border-collapse: collapse;
    width: 75%;
}
tr {
    border-bottom: 1px solid #000;
}
th {
    background: #ccc;
}
td, th {
    padding: 1%;
    margin: 1%;
    border: 1px solid #000;
}
</style>
