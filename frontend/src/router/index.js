import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Projects from '../views/Projects.vue'
import Groups from '../views/Groups.vue'
import Users from '../views/Users.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/projects',
    name: 'Projects',
    component: Projects
  },
  {
    path: '/groups',
    name: 'Groups',
    component: Groups
  },
  {
    path: '/users',
    name: 'Users',
    component: Users
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  base: import.meta.env.BASE_URL,
  routes,
});


export default router
