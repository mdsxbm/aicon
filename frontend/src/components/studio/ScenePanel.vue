<template>
  <div class="scene-panel">
    <div class="panel-header">
      <h3>场景列表</h3>
      <div class="actions">
        <el-button 
          type="primary"
          :loading="extracting"
          :disabled="!canExtract"
          @click="$emit('extract-scenes')"
        >
          提取场景
        </el-button>
      </div>
    </div>

    <div class="scene-list">
      <el-empty v-if="scenes.length === 0" description="暂无场景，请先提取场景" />
      
      <el-collapse v-else v-model="activeScenes">
        <el-collapse-item 
          v-for="scene in scenes" 
          :key="scene.id"
          :name="scene.id"
        >
          <template #title>
            <div class="scene-title">
              <span class="scene-number">场景 {{ scene.order_index }}</span>
              <el-tag 
                v-for="char in scene.characters" 
                :key="char"
                size="small"
                type="info"
                style="margin-left: 8px"
              >
                {{ char }}
              </el-tag>
            </div>
          </template>
          
          <div class="scene-content">
            <p>{{ scene.scene }}</p>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  scenes: {
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

defineEmits(['extract-scenes'])

const activeScenes = ref([])
</script>

<style scoped>
.scene-panel {
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

.scene-title {
  display: flex;
  align-items: center;
  flex: 1;
}

.scene-number {
  font-weight: 600;
  color: #409eff;
}

.scene-content {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
}

.scene-content p {
  margin: 0;
  white-space: pre-wrap;
}
</style>
