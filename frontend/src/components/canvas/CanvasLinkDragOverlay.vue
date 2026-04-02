<template>
  <div v-if="path" class="canvas-link-drag-layer">
    <svg class="canvas-link-drag-layer__svg">
      <path :d="path" class="canvas-link-drag-layer__path" />
    </svg>
  </div>
</template>

<script setup>
defineProps({
  path: { type: String, default: '' }
})
</script>

<style scoped>
.canvas-link-drag-layer {
  position: absolute;
  inset: 0;
  z-index: 17;
  pointer-events: none;
}

.canvas-link-drag-layer__svg {
  width: 100%;
  height: 100%;
}

.canvas-link-drag-layer__path {
  fill: none;
  stroke: rgba(75, 120, 255, 0.9);
  stroke-width: 2.4px;
  stroke-linecap: round;
  filter: drop-shadow(0 0 12px rgba(75, 120, 255, 0.24));
}
</style>
