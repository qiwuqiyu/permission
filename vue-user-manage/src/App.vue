<!-- App.vue 瘦身为纯入口：页面都交给路由渲染，逻辑移到了 views/ 目录 -->
<template>
  <!-- router-view = 路由出口：URL 对应哪个页面组件，就在这里显示哪个 -->
  <!-- 类比：App.vue 从"住户"变成了"房管局"，只负责按地址分发 -->
  <router-view />
</template>

<script setup>
</script>
