<template>
  <el-drawer
    :model-value="visible"
    :title="title"
    size="560px"
    append-to-body
    @close="emit('update:visible', false)"
  >
    <div class="history-drawer">
      <div v-if="subtitle" class="history-drawer__subtitle">{{ subtitle }}</div>

      <div class="history-drawer__actions">
        <el-button text @click="emit('refresh')">刷新</el-button>
      </div>

      <div v-loading="loading" class="history-drawer__body">
        <el-empty v-if="!items.length" description="暂无历史记录" />

        <div v-else class="history-drawer__list">
          <article
            v-for="item in items"
            :key="item.id"
            class="history-card"
            :class="{ 'history-card--active': item.isActive }"
          >
            <div class="history-card__preview">
              <img
                v-if="mediaType === 'image' && item.previewUrl"
                :src="item.previewUrl"
                :alt="item.prompt || 'history preview'"
              />
              <video
                v-else-if="mediaType === 'video' && item.previewUrl"
                :src="item.previewUrl"
                controls
                playsinline
                preload="metadata"
              ></video>
              <div v-else class="history-card__empty-preview">无预览</div>
            </div>

            <div class="history-card__content">
              <div class="history-card__meta">
                <el-tag size="small" :type="item.isActive ? 'success' : 'info'">
                  {{ item.isActive ? '当前版本' : item.statusText }}
                </el-tag>
                <span class="history-card__time">{{ item.createdAtText }}</span>
              </div>

              <div class="history-card__prompt">
                {{ item.prompt || '未记录提示词' }}
              </div>

              <div class="history-card__footer">
                <span class="history-card__model">{{
                  item.model || '未记录模型'
                }}</span>
                <el-button
                  v-if="!item.isActive"
                  type="primary"
                  size="small"
                  :loading="selectingId === item.id"
                  @click="emit('select', item)"
                >
                  使用此版本
                </el-button>
              </div>
            </div>
          </article>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
  defineProps({
    visible: { type: Boolean, default: false },
    title: { type: String, default: '历史记录' },
    subtitle: { type: String, default: '' },
    items: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    selectingId: { type: String, default: '' },
    mediaType: {
      type: String,
      default: 'image',
      validator: (value) => ['image', 'video'].includes(value)
    }
  })

  const emit = defineEmits(['update:visible', 'refresh', 'select'])
</script>

<style scoped>
  .history-drawer {
    display: flex;
    flex-direction: column;
    min-height: 100%;
  }

  .history-drawer__subtitle {
    margin-bottom: 12px;
    color: #5f6b85;
    font-size: 13px;
    line-height: 1.5;
  }

  .history-drawer__actions {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 12px;
  }

  .history-drawer__body {
    flex: 1;
    min-height: 240px;
  }

  .history-drawer__list {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .history-card {
    display: grid;
    grid-template-columns: 180px minmax(0, 1fr);
    gap: 14px;
    padding: 14px;
    border: 1px solid rgba(31, 49, 88, 0.12);
    border-radius: 18px;
    background: linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.98),
      rgba(246, 249, 255, 0.95)
    );
  }

  .history-card--active {
    border-color: rgba(45, 170, 104, 0.5);
    box-shadow: inset 0 0 0 1px rgba(45, 170, 104, 0.18);
  }

  .history-card__preview {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 120px;
    border-radius: 14px;
    overflow: hidden;
    background: rgba(227, 234, 247, 0.7);
  }

  .history-card__preview img,
  .history-card__preview video {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .history-card__empty-preview {
    color: #71809c;
    font-size: 13px;
  }

  .history-card__content {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .history-card__meta,
  .history-card__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .history-card__time,
  .history-card__model {
    color: #71809c;
    font-size: 12px;
  }

  .history-card__prompt {
    color: #24314d;
    font-size: 14px;
    line-height: 1.6;
    word-break: break-word;
    display: -webkit-box;
    overflow: hidden;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
  }

  @media (max-width: 720px) {
    .history-card {
      grid-template-columns: 1fr;
    }
  }
</style>
