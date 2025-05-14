// frontend/src/components/layout/Sidebar.vue
<template>
  <div> 
    <div class="logo-container">
      <img src="@/assets/logo.png" alt="Logo" class="logo-img" v-if="logoVisible" />
      <h1 class="sidebar-title" v-if="!isCollapse">量化助手</h1>
    </div>
    <el-scrollbar wrap-class="scrollbar-wrapper">
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical-demo"
        :collapse="isCollapse"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item v-for="route in menuRoutes" :key="route.path" :index="resolvePath(route.path)">
          <el-icon v-if="route.meta && route.meta.icon"><component :is="route.meta.icon" /></el-icon>
          <template #title>{{ route.meta && route.meta.title }}</template>
        </el-menu-item>
        <!-- 分隔线等 -->
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<script setup>
// ... (您现有的 script setup 内容保持不变) ...
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const isCollapse = ref(false);
const logoVisible = ref(true); // 确保 logoVisible 已定义

const activeMenu = computed(() => {
  const { meta, path } = route;
  if (meta?.activeMenu) { // 确保 meta 存在
    return meta.activeMenu;
  }
  return path;
});

const menuRoutes = computed(() => {
  return router.options.routes.find(r => r.path === '/')?.children?.filter(child => child.meta && child.meta.title) || [];
});

const resolvePath = (path) => {
  if (!path) return '/'; // 添加一个默认值或错误处理
  if (path.startsWith('/')) return path;
  return `/${path}`;
}
</script>

<style scoped>
/* ... (您现有的 style scoped 内容保持不变) ... */
.logo-container {
  height: 50px;
  line-height: 50px;
  background: #2b2f3a;
  text-align: center;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.logo-img {
  width: 32px;
  height: 32px;
  vertical-align: middle;
  margin-right: 12px;
}
.sidebar-title {
  display: inline-block;
  margin: 0;
  color: #fff;
  font-weight: 600;
  line-height: 50px;
  font-size: 16px;
  font-family: Avenir, Helvetica Neue, Arial, Helvetica, sans-serif;
  vertical-align: middle;
}
.el-menu-vertical-demo:not(.el-menu--collapse) {
  /* width: 220px; */ /* 由 AppLayout.vue 中的 el-aside 控制宽度 */
  min-height: 400px;
}
.el-menu {
  border-right: none;
}
.el-scrollbar {
  height: calc(100% - 50px); /* 减去logo高度 */
}
.scrollbar-wrapper {
  overflow-x: hidden !important;
}
</style>