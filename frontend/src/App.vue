<template>
  <div id="app">
    <div id="nav">
      <h1>Congregate</h1>
      <router-link to="/">Home</router-link>
      <router-link to="/projects">Projects</router-link>
      <router-link to="/groups">Groups</router-link>
      <router-link to="/users">Users</router-link>
    </div>
    <div id = "content">
      <router-view/>
    </div>
  </div>
</template>

<style lang="less">
#app {
  font-family: Arial, Helvetica, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  color: #111;
  position: absolute;
  width: 100%;
  height: 100%;
  background-repeat: no-repeat;
  background-attachment: fixed;
  background-position: center;
}

#nav {
  background-color: #FF851B;
  color :hsl(28, 100%, 20%);
  position: fixed;
  width: 10%;
  height: 100%;
  text-align: left;

  h1 {
    font-size: 1.5em;
    text-indent: 0.5em;
    padding: 0.5em 0;
  }

  a {
    font-weight: bold;
    color: hsl(28, 100%, 20%);
    display: block;
    text-indent: 0.5em;
    padding: 0.5em 0;

    &.router-link-exact-active {
      background-color: hsl(28, 100%, 20%);
      color: #FF851B;
    }

    &:link {
      display: block;
      padding: 0.5em 0;
      text-decoration-line: none;
      width: 100%;
    }

    &:hover {
      background-color: hsl(28, 100%, 20%);
      color: #FF851B;
      text-decoration-line: underline;
    }

    p {
      margin-left: 0.5em;
    }
  }

}

#content {
  position: relative;
  left: 10%;
  right: 10%;
  width: 85%;
  padding-top: 1em;
  color: #111;
}

#content h1 {
  font-size: 1.5em;
  display: inline;
  border: 1px solid #FF851B;
  border-bottom: none;
  padding: 0.05em 0.2em;
}

.table {
  padding: 1em;
}

.summary-list {
  li {
    list-style: none;
    text-align: left;
    padding: 1em;
    background: #ccc;
    border-top: 1px solid #000;
  }
  table {
    border-spacing: 1px;
    border-collapse: separate;
    td, th {
      padding: 1em;
      border: 1px solid #000;
    }
  }
}
</style>
