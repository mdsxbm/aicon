<template>
  <div v-if="visible && position" class="connection-actions">
    <button
      class="connection-control-btn"
      type="button"
      :style="{ left: `${position.x - 14}px`, top: `${position.y - 14}px` }"
      @mousedown.stop="$emit('delete')"
    >
      <el-icon><Close /></el-icon>
    </button>
  </div>
</template>

<script setup>
import { Close } from '@element-plus/icons-vue'

defineProps({
  visible: { type: Boolean, default: false },
  position: { type: Object, default: null }
})

defineEmits(['delete'])
</script>

<style scoped>
.connection-control-btn {
  position: absolute;
  z-index: 20;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(8px);
  color: rgba(255, 120, 117, 0.9);
  border: 1px solid rgba(255, 120, 117, 0.3);
  box-shadow: 0 10px 20px rgba(34, 57, 98, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.connection-control-btn:hover {
  transform: scale(1.15);
  background: rgba(255, 77, 79, 0.08);
  color: #ff4d4f;
}
</style>
