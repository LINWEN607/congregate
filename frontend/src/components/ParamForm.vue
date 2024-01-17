<template>
    <form :id="formId">
        <details>
            <summary>Parameters</summary>
                <ul>
                    <li v-for="item in params">
                        <input type="checkbox" :id="item.param" :name="item.param"><label :for="item.param">{{ item.label }}</label>
                    </li>
                </ul>
        </details>
    </form>
</template>
<script>
export default {
  name: 'ParamForm',
  props: {
    params: Array,
    formId: String
  },
}
</script>

<style scoped>
form {
    font-size: 0.8em;
}
details:hover {
    cursor: pointer;
}
ul {
    list-style-type: none;
    margin: 0;
    padding-left: 0;
}
ul:hover {
    cursor: auto;
}
</style>
