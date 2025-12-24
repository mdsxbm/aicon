<template>
  <div class="character-panel">
    <div class="panel-header">
      <h3>角色管理</h3>
      <div class="actions">
        <el-button 
          type="primary" 
          :loading="extracting"
          :disabled="!canExtract"
          @click="$emit('extract-characters')"
        >
          提取角色
        </el-button>
        <el-button 
          type="success"
          :disabled="characters.length === 0"
          @click="$emit('batch-generate')"
        >
          批量生成形象
        </el-button>
      </div>
    </div>

    <div class="character-list">
      <el-empty v-if="characters.length === 0" description="暂无角色，请先提取角色" />
      
      <div v-else class="character-grid">
        <div 
          v-for="char in characters" 
          :key="char.id"
          class="character-card"
        >
          <div class="character-avatar">
            <img v-if="char.avatar_url" :src="char.avatar_url" :alt="char.name" />
            <div v-else class="avatar-placeholder">
              <el-icon :size="40"><User /></el-icon>
            </div>
          </div>
          
          <div class="character-info">
            <h4>{{ char.name }}</h4>
            <p class="role">{{ char.role }}</p>
            <p class="traits">{{ char.visual_traits }}</p>
          </div>

          <div class="character-actions">
            <el-button 
              v-if="!char.avatar_url"
              type="primary" 
              size="small"
              :loading="generatingId === char.id"
              @click="$emit('generate-avatar', char)"
            >
              生成形象
            </el-button>
            <el-button 
              v-else
              type="success" 
              size="small"
              icon="Check"
              disabled
            >
              已生成
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              icon="Delete"
              @click="$emit('delete-character', char)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { User } from '@element-plus/icons-vue'

defineProps({
  characters: {
    type: Array,
    default: () => []
  },
  extracting: {
    type: Boolean,
    default: false
  },
  generatingId: {
    type: String,
    default: null
  },
  canExtract: {
    type: Boolean,
    default: true
  }
})

defineEmits(['extract-characters', 'generate-avatar', 'delete-character', 'batch-generate'])
</script>

<style scoped>
.character-panel {
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

.character-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.character-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
}

.character-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.character-avatar {
  width: 100%;
  height: 160px;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.character-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  color: #c0c4cc;
}

.character-info h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
}

.character-info .role {
  margin: 0 0 4px 0;
  font-size: 13px;
  color: #606266;
}

.character-info .traits {
  margin: 0;
  font-size: 12px;
  color: #909399;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.character-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.character-actions .el-button {
  flex: 1;
}
</style>
