<template>
  <div class="keyframe-panel">
    <div class="panel-header">
      <h3>关键帧预览</h3>
      <div class="actions">
        <el-button 
          type="primary"
          :loading="generating"
          :disabled="!canGenerate"
          @click="$emit('generate-keyframes')"
        >
          生成关键帧
        </el-button>
      </div>
    </div>

    <div class="keyframe-grid">
      <el-empty v-if="shots.length === 0" description="暂无分镜，请先提取分镜" />
      
      <div v-else class="grid">
        <div 
          v-for="shot in shots" 
          :key="shot.id"
          class="keyframe-item"
        >
          <div class="keyframe-image">
            <img v-if="shot.keyframe_url" :src="shot.keyframe_url" :alt="`分镜${shot.order_index}`" />
            <div v-else class="placeholder">
              <el-icon :size="40"><Picture /></el-icon>
              <span>未生成</span>
            </div>
          </div>
          
          <div class="keyframe-info">
            <span class="shot-number">分镜 {{ shot.order_index }}</span>
            <el-tag 
              v-if="shot.keyframe_url" 
              type="success" 
              size="small"
            >
              已生成
            </el-tag>
            <el-tag 
              v-else 
              type="info" 
              size="small"
            >
              待生成
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Picture } from '@element-plus/icons-vue'

defineProps({
  shots: {
    type: Array,
    default: () => []
  },
  generating: {
    type: Boolean,
    default: false
  },
  canGenerate: {
    type: Boolean,
    default: true
  }
})

defineEmits(['generate-keyframes'])
</script>

<style scoped>
.keyframe-panel {
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

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.keyframe-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
}

.keyframe-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.keyframe-image {
  width: 100%;
  aspect-ratio: 16/9;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.keyframe-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #c0c4cc;
}

.placeholder span {
  font-size: 12px;
}

.keyframe-info {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.shot-number {
  font-weight: 600;
  font-size: 13px;
  color: #606266;
}
</style>
