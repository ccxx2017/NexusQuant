<template>
  <el-container class="app-layout-container">
    <el-aside width="220px" class="sidebar-container">
      <Sidebar />
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <!-- 可选的顶部栏内容 -->
      </el-header>
      <el-main class="app-main-content">
        <router-view v-slot="{ Component }"> 
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import Sidebar from './Sidebar.vue'; // 确保 Sidebar 组件导入正确
</script>

<style scoped>
.app-layout-container {
  height: 100vh;
}
.sidebar-container {
  background-color: #304156; /* 深色侧边栏示例 */
  /* color: #bfcbd9; */
}
.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  padding: 0 20px;
}
.app-main-content {
  background-color: #f0f2f5; /* 内容区背景色示例 */
  padding: 20px;
  overflow-y: auto;
}

/* 路由切换动画 */
.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all .3s;
}
.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}
.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>