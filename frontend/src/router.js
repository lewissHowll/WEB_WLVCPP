import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Contact from './views/Contact.vue'

const routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/contact', name: 'contact', component: Contact },
]

export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})
