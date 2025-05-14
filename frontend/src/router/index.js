// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue' // 确保这个路径是正确的，并且 AppLayout.vue 存在且可被解析

const routes = [
  {
    path: '/', // 根路径
    component: AppLayout, // <--- 非常重要：根路径应该渲染 AppLayout 组件
    redirect: '/dashboard', // <--- 重要：访问根路径时，重定向到 /dashboard
    children: [ // AppLayout 的子路由，会渲染在 AppLayout 内部的 <router-view />
      {
        path: 'dashboard', // 实际路径是 /dashboard
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '主仪表盘', icon: 'House' }
      },
      {
        path: 'selection-engine', // /selection-engine
        name: 'SelectionEngine',
        component: () => import('@/views/selection/SelectionEngineView.vue'),
        meta: { title: '智能灯塔 · 选品', icon: 'Aim' }
      },
      {
        path: 'timing-engine', // /timing-engine
        name: 'TimingEngine',
        component: () => import('@/views/timing/TimingEngineView.vue'),
        meta: { title: '黄金窗口 · 择时', icon: 'Opportunity' }
      },
      {
        path: 'exit-engine', // /exit-engine
        name: 'ExitEngine',
        component: () => import('@/views/exit/ExitEngineView.vue'),
        meta: { title: '幻方黑匣 · 退出', icon: 'SwitchButton' }
      },
      {
        path: 'backtesting-lab', // /backtesting-lab
        name: 'BacktestingLab',
        component: () => import('@/views/backtesting/BacktestingLabView.vue'),
        meta: { title: '策略实验室 · 回测', icon: 'DataAnalysis' }
      },
    ]
  },
  // (可选) 可以添加一个404页面
  // {
  //   path: '/:catchAll(.*)', // 匹配所有未定义的路径
  //   name: 'NotFound',
  //   component: () => import('@/views/NotFoundView.vue') // 需要创建 NotFoundView.vue
  // }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL), // 确保 BASE_URL 配置正确 (通常是 '/')
  routes
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} - 三位一体量化助手` || '三位一体量化助手';
  next();
});

export default router