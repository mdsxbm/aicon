<template>
  <div
    v-if="visible"
    class="link-create-menu"
    :style="{ left: `${screenX}px`, top: `${screenY}px` }"
  >
    <div class="link-create-menu__header">{{ title }}</div>
    <button
      v-for="option in options"
      :key="option.type"
      class="link-create-menu__item"
      type="button"
      @click="$emit('select', option.type)"
    >
      <span class="link-create-menu__item-title">{{ option.label }}</span>
      <span class="link-create-menu__item-desc">{{ option.description }}</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '创建并连接节点' },
  options: { type: Array, default: () => [] },
  screenX: { type: Number, default: 0 },
  screenY: { type: Number, default: 0 }
})

defineEmits(['select'])
</script>

<style scoped>
.link-create-menu {
  position: absolute;
  z-index: 21;
  width: 228px;
  padding: 10px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(34, 57, 98, 0.08);
  box-shadow: 0 18px 30px rgba(34, 57, 98, 0.12), 0 26px 42px rgba(34, 57, 98, 0.1);
  backdrop-filter: blur(18px);
}

.link-create-menu__header {
  padding: 4px 6px 10px;
  color: #667085;
  font-size: 11px;
  font-weight: 600;
}

.link-create-menu__item {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border: none;
  border-radius: 14px;
  background: transparent;
  color: #1f2a44;
  text-align: left;
  cursor: pointer;
}

.link-create-menu__item:hover {
  background: #f4f7fb;
}

.link-create-menu__item-title {
  font-size: 13px;
  font-weight: 600;
}

.link-create-menu__item-desc {
  color: #667085;
  font-size: 11px;
  line-height: 1.4;
}
</style>
