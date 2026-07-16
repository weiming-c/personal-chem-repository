import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomePage.vue'),
    },
    {
      path: '/questions',
      name: 'questionList',
      component: () => import('@/views/QuestionList.vue'),
    },
    {
      path: '/questions/new',
      name: 'questionCreate',
      component: () => import('@/views/QuestionEdit.vue'),
    },
    {
      path: '/questions/:id',
      name: 'questionDetail',
      component: () => import('@/views/QuestionDetail.vue'),
    },
    {
      path: '/questions/:id/edit',
      name: 'questionEdit',
      component: () => import('@/views/QuestionEdit.vue'),
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/SearchPage.vue'),
    },
    {
      path: '/wrong-questions',
      name: 'wrongQuestions',
      component: () => import('@/views/WrongQuestions.vue'),
    },
    {
      path: '/papers',
      name: 'paperList',
      component: () => import('@/views/PaperList.vue'),
    },
    {
      path: '/papers/new',
      name: 'paperConfig',
      component: () => import('@/views/PaperConfig.vue'),
    },
    {
      path: '/papers/:id/practice',
      name: 'practice',
      component: () => import('@/views/PracticePage.vue'),
    },
    {
      path: '/tags',
      name: 'tagManage',
      component: () => import('@/views/TagManage.vue'),
    },
  ],
})

export default router
