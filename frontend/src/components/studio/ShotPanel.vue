<template>
  <div class="shot-panel">
    <div class="panel-header">
      <h3>分镜列表</h3>
      <div class="actions">
        <el-button 
          type="primary"
          :loading="extracting"
          :disabled="!canExtract"
          @click="$emit('extract-shots')"
        >
          提取分镜
        </el-button>
      </div>
    </div>

    <div class="shot-list">
      <el-empty v-if="shots.length === 0" description="暂无分镜，请先提取分镜" />
      
      <div v-else class="shot-grid">
        <div 
          v-for="shot in shots" 
          :key="shot.id"
          class="shot-card"
        >
          <div class="shot-header">
            <span class="shot-number">分镜 {{ shot.order_index }}</span>
            <el-tag v-if="shot.camera_movement" size="small" type="warning">
              {{ shot.camera_movement }}
            </el-tag>
          </div>

          <div class="shot-characters">
            <el-tag 
              v-for="char in shot.characters" 
              :key="char"
              size="small"
              type="info"
            >
              {{ char }}
            </el-tag>
          </div>

          <div class="shot-description">
            <p>{{ shot.visual_description }}</p>
          </div>

          <div v-if="shot.dialogue" class="shot-dialogue">
            <el-icon><ChatDotRound /></el-icon>
            <span>{{ shot.dialogue }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ChatDotRound } from '@element-plus/icons-vue'

defineProps({
  shots: {
    type: Array,
    default: () => []
  },
  extracting: {
    type: Boolean,
    default: false
  },
  canExtract: {
    type: Boolean,
    default: true
  }
})

defineEmits(['extract-shots'])
</script>

<style scoped>
.shot-panel {
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

.shot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.shot-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
}

.shot-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.shot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.shot-number {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
}

.shot-characters {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.shot-description {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.shot-description p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}

.shot-dialogue {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  background: #ecf5ff;
  border-radius: 4px;
  font-size: 12px;
  color: #409eff;
}

.shot-dialogue .el-icon {
  flex-shrink: 0;
  margin-top: 2px;
}
</style>
