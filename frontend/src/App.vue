<script setup>
import ToastContainer from './components/ToastContainer.vue'
</script>

<template>
  <div class="app-shell">
    <main class="container app-shell__main">
      <router-view />
    </main>
    <ToastContainer />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.app-shell__main {
  flex: 1;
  padding-bottom: var(--space-8);
}
</style>
