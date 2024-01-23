<template>
    <div class='action-card'>
      <div class='action-card-title'>{{ title }}</div>
      <div class='action-card-content'>
        <slot></slot>
      </div>
    </div>
</template>

<script>
export default {
  name: 'ActionCard',
  props: ['title']
}
</script>

<style scoped>
.action-card {
    text-align: left;
    padding: 1% 0;
}
.action-card-title {
    border: 1px solid #663000;
    margin: 0;
    margin-bottom: -1px;
    display: inline-block;
    font-weight: bold;
    padding: 0.5em 0.5em 0.5em 0.25em;
    background-color: #FF851B;
}
.action-card-content {
    border: 1px solid #663000;
    background-color: #fff;
    padding: 1em;
}

button {
  cursor: pointer;
  background-color: #ccc;
  border: 1px solid #666;
  border-radius: 5px;
}

button:hover {
  background-color: #aaa;
}
  
</style>
