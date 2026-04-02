<template>
  <div class="canvas-workbench-layout">
    <div class="canvas-topbar" :class="{ 'is-assistant-expanded': assistantExpanded }">
      <button class="brand-chip" type="button" @click="$emit('back')">
        <span class="brand-chip__title">{{ title }}</span>
      </button>

      <div class="topbar-actions">
        <button class="topbar-pill" type="button" @click="$emit('save')">
          <span class="topbar-pill__value">{{ saveLabel }}</span>
        </button>
      </div>
    </div>

    <aside class="left-toolbar-panel">
      <el-dropdown trigger="click" placement="right-start" popper-class="canvas-create-dropdown" @command="handleMenuCommand">
        <button class="toolbar-btn toolbar-btn--primary" type="button" :disabled="creatingItem">
          <el-icon><Plus /></el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <div class="canvas-dropdown-header">
              <el-icon class="header-icon"><Plus /></el-icon>
              <span>新建节点类型</span>
            </div>
            <el-dropdown-item command="text">
              <div class="canvas-dropdown-item">
                <div class="item-title">文本节点</div>
                <div class="item-desc">创建文本内容节点</div>
              </div>
            </el-dropdown-item>
            <el-dropdown-item command="image">
              <div class="canvas-dropdown-item">
                <div class="item-title">图片节点</div>
                <div class="item-desc">创建图片内容节点</div>
              </div>
            </el-dropdown-item>
            <el-dropdown-item command="video">
              <div class="canvas-dropdown-item">
                <div class="item-title">视频节点</div>
                <div class="item-desc">创建视频内容节点</div>
              </div>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <div class="toolbar-icons-group">
        <button class="toolbar-btn" type="button" :disabled="creatingItem" @click="$emit('create-item', 'text')">
          <el-icon><Document /></el-icon>
        </button>
        <button class="toolbar-btn" type="button" :disabled="creatingItem" @click="$emit('create-item', 'image')">
          <el-icon><Picture /></el-icon>
        </button>
        <button class="toolbar-btn" type="button" :disabled="creatingItem" @click="$emit('create-item', 'video')">
          <el-icon><VideoPlay /></el-icon>
        </button>
      </div>
    </aside>

    <aside class="assistant-rail">
      <div class="assistant-rail__surface">
        <slot />
      </div>
    </aside>

    <div class="zoom-panel">
      <div class="zoom-hint">{{ zoomHintText }}</div>
    </div>

    <div v-if="linkModeText" class="link-mode-toast">
      {{ linkModeText }}
    </div>
  </div>
</template>

<script setup>
import { Document, Picture, Plus, VideoPlay } from '@element-plus/icons-vue'

const props = defineProps({
  title: { type: String, default: '' },
  saveLabel: { type: String, default: '保存' },
  zoomHintText: { type: String, default: '' },
  linkModeText: { type: String, default: '' },
  creatingItem: { type: Boolean, default: false },
  assistantExpanded: { type: Boolean, default: true }
})

const emit = defineEmits(['back', 'save', 'create-item'])

const handleMenuCommand = (command) => {
  emit('create-item', command)
}
</script>

<style scoped>
.canvas-workbench-layout {
  position: absolute;
  inset: 0;
  --canvas-assistant-rail-width: min(420px, calc(100vw - 132px));
  pointer-events: none;
}

.canvas-topbar {
  position: absolute;
  top: 20px;
  left: 24px;
  right: 24px;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  transition: right 0.35s cubic-bezier(0.25, 1, 0.5, 1);
  pointer-events: none;
}

.canvas-topbar.is-assistant-expanded {
  right: calc(var(--canvas-assistant-rail-width) + 24px);
}

.brand-chip,
.topbar-pill,
.toolbar-btn {
  border: none;
  cursor: pointer;
  pointer-events: auto;
}

.brand-chip {
  display: inline-flex;
  align-items: center;
  background: transparent;
  padding: 0;
}

.brand-chip__title {
  color: #1f2a44;
  font-size: 15px;
  font-weight: 600;
}

.topbar-pill {
  display: inline-flex;
  align-items: center;
  height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(34, 57, 98, 0.1);
  color: #1f2a44;
  box-shadow: 0 10px 30px rgba(34, 57, 98, 0.08);
}


.topbar-pill__value {
  font-size: 14px;
  font-weight: 700;
}

.assistant-rail {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 24;
  width: var(--canvas-assistant-rail-width);
  display: flex;
  justify-content: flex-end;
  pointer-events: none;
}

.assistant-rail__surface {
  width: 100%;
  min-width: 0;
  min-height: 0;
  display: flex;
  pointer-events: auto;
}

.left-toolbar-panel {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 18;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(34, 57, 98, 0.08);
  border-radius: 999px;
  padding: 10px 6px;
  gap: 16px;
  box-shadow: 0 14px 32px rgba(34, 57, 98, 0.1);
  pointer-events: auto;
}

.toolbar-icons-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.toolbar-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f6fb;
  color: #52607a;
}

.toolbar-btn:hover:not(:disabled) {
  background: #e7edf8;
  color: #1f2a44;
}

.toolbar-btn--primary {
  width: 44px;
  height: 44px;
  background: linear-gradient(180deg, #4b78ff, #355ce0);
  color: #fff;
}

.zoom-panel {
  position: absolute;
  left: 14px;
  bottom: 14px;
  z-index: 18;
  pointer-events: none;
}

.zoom-hint {
  max-width: 340px;
  padding: 10px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.94);
  color: #52607a;
  font-size: 12px;
  border: 1px solid rgba(34, 57, 98, 0.08);
  box-shadow: 0 10px 24px rgba(34, 57, 98, 0.08);
  pointer-events: auto;
}

.link-mode-toast {
  position: absolute;
  left: 50%;
  top: 92px;
  transform: translateX(-50%);
  z-index: 19;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(75, 120, 255, 0.18);
  color: #355ce0;
  box-shadow: 0 12px 24px rgba(75, 120, 255, 0.12);
  font-size: 12px;
  pointer-events: auto;
}
</style>

<style>
.canvas-create-dropdown {
  background: rgba(255, 255, 255, 0.98) !important;
  border: 1px solid rgba(34, 57, 98, 0.08) !important;
  border-radius: 14px !important;
  padding: 8px !important;
  box-shadow: 0 18px 40px rgba(34, 57, 98, 0.12) !important;
}

.canvas-create-dropdown .el-dropdown-menu {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.canvas-dropdown-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 14px;
  font-size: 13px;
  color: #667085;
  font-weight: 600;
  border-bottom: 1px solid rgba(34, 57, 98, 0.08);
  margin-bottom: 8px;
}

.canvas-dropdown-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
