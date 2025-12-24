<template>
  <div class="transition-panel">
    <div class="panel-header">
      <h3>过渡视频</h3>
      <div class="actions">
        <el-button 
          type="primary"
          :loading="creating"
          :disabled="!canCreate"
          @click="$emit('create-transitions')"
        >
          创建过渡
        </el-button>
        <el-button 
          type="success"
          :loading="generating"
          :disabled="!canGenerate"
          @click="$emit('generate-videos')"
        >
          生成视频
        </el-button>
      </div>
    </div>

    <div class="transition-list">
      <el-empty v-if="transitions.length === 0" description="暂无过渡，请先创建过渡" />
      
      <div v-else class="transition-grid">
        <div 
          v-for="transition in transitions" 
          :key="transition.id"
          class="transition-card"
        >
          <div class="transition-header">
            <span class="transition-label">过渡 {{ transition.order_index }}</span>
            <el-tag 
              :type="getStatusType(transition.status)" 
              size="small"
            >
              {{ getStatusText(transition.status) }}
            </el-tag>
          </div>

          <div class="transition-frames">
            <div class="frame">
              <img v-if="transition.from_shot_keyframe" :src="transition.from_shot_keyframe" alt="起始帧" />
              <div v-else class="frame-placeholder">起始帧</div>
            </div>
            <div class="arrow">
              <el-icon><Right /></el-icon>
            </div>
            <div class="frame">
              <img v-if="transition.to_shot_keyframe" :src="transition.to_shot_keyframe" alt="结束帧" />
              <div v-else class="frame-placeholder">结束帧</div>
            </div>
          </div>

          <div v-if="transition.video_prompt" class="transition-prompt">
            <p>{{ transition.video_prompt }}</p>
          </div>

          <div v-if="transition.video_url" class="transition-video">
            <video :src="transition.video_url" controls />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Right } from '@element-plus/icons-vue'

defineProps({
  transitions: {
    type: Array,
    default: () => []
  },
  creating: {
    type: Boolean,
    default: false
  },
  generating: {
    type: Boolean,
    default: false
  },
  canCreate: {
    type: Boolean,
    default: true
  },
  canGenerate: {
    type: Boolean,
    default: false
  }
})

defineEmits(['create-transitions', 'generate-videos'])

const getStatusType = (status) => {
  const map = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    'pending': '待生成',
    'processing': '生成中',
    'completed': '已完成',
    'failed': '失败'
  }
  return map[status] || status
}
</script>

<style scoped>
.transition-panel {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 10px;
}

.transition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.transition-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
}

.transition-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.transition-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.transition-label {
  font-weight: 600;
  color: #409eff;
}

.transition-frames {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.frame {
  flex: 1;
  aspect-ratio: 16/9;
  border-radius: 4px;
  overflow: hidden;
  background: #f5f7fa;
}

.frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.frame-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 12px;
}

.arrow {
  color: #409eff;
  font-size: 20px;
}

.transition-prompt {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
}

.transition-prompt p {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: #606266;
}

.transition-video {
  border-radius: 4px;
  overflow: hidden;
}

.transition-video video {
  width: 100%;
  display: block;
}
</style>
