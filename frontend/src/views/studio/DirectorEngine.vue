<template>
  <div class="director-mode">
    <div class="toolbar">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="选择章节" style="width: 300px">
          <el-select v-model="selectedChapterId" placeholder="请选择已确认的章节" @change="loadSentences">
            <el-option
              v-for="chapter in chapters"
              :key="chapter.id"
              :label="`第${chapter.chapter_number}章: ${chapter.title} (${chapter.status})`"
              :value="chapter.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item v-if="selectedChapterId">
          <el-button type="primary" @click="dialogVisible = true">
            生成分镜脚本
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 生成提示词对话框 -->
      <el-dialog
        v-model="dialogVisible"
        title="生成分镜脚本"
        width="500px"
      >
        <el-form :inline="false" class="dialog-form">
          <el-form-item label="API Key" style="width: 100%">
            <el-select v-model="selectedApiKey" placeholder="选择API Key" style="width: 100%">
              <el-option
                v-for="key in apiKeys"
                :key="key.id"
                :label="key.name + ' (' + key.provider + ')'"
                :value="key.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="风格" style="width: 100%">
            <el-select v-model="selectedStyle" placeholder="选择风格" style="width: 100%">
              <el-option label="电影质感 (Cinematic)" value="cinematic" />
              <el-option label="二次元 (Anime)" value="anime" />
              <el-option label="插画 (Illustration)" value="illustration" />
              <el-option label="水墨 (Ink)" value="ink" />
            </el-select>
          </el-form-item>
        </el-form>
        
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="generating" @click="generatePrompts">
              生成
            </el-button>
          </span>
        </template>
      </el-dialog>
    </div>

    <div class="content-area" v-loading="loading">
      <el-empty v-if="!sentences.length" description="请选择章节以开始" />
      
      <div v-else class="sentence-list">
        <div v-for="(sentence, index) in sentences" :key="sentence.id" class="sentence-item">
          <div class="sentence-header">
            <span class="index">#{{ index + 1 }}</span>
            <span class="text">{{ sentence.content }}</span>
          </div>
          
          <div class="prompt-editor">
            <div class="label">图片 Prompt:</div>
            <el-input
              v-model="sentence.image_prompt"
              type="textarea"
              :rows="3"
              placeholder="等待生成..."
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import chaptersService from '@/services/chapters'
import apiKeysService from '@/services/apiKeys'
import api from '@/services/api'

const route = useRoute()

// Props
const props = defineProps({
  projectId: {
    type: String,
    required: true
  }
})

const chapters = ref([])
const apiKeys = ref([])
const sentences = ref([])
const selectedChapterId = ref('')
const selectedApiKey = ref('')
const selectedStyle = ref('cinematic')
const loading = ref(false)
const generating = ref(false)
const dialogVisible = ref(false)

// 加载已确认的章节
const loadChapters = async () => {
  try {
    const res = await chaptersService.getConfirmedChapters(props.projectId)
    chapters.value = res.chapters || []

    // 如果URL中有chapterId参数，自动选中该章节
    const chapterIdFromQuery = route.query.chapterId
    if (chapterIdFromQuery) {
      selectedChapterId.value = chapterIdFromQuery
      // 自动加载该章节的句子
      await loadSentences()
    }
  } catch (error) {
    console.error('加载章节失败', error)
  }
}

// 加载API Keys (模拟，实际应从API获取)
const loadApiKeys = async () => {
  const res = await apiKeysService.getAPIKeys()
  apiKeys.value = res.api_keys || []
}

// 加载句子 - 使用优化的批量接口
const loadSentences = async () => {
  if (!selectedChapterId.value) return
  
  loading.value = true
  try {
    // 使用新的批量接口，一次性获取所有句子
    const response = await api.get(`/chapters/${selectedChapterId.value}/sentences`)
    sentences.value = response.sentences || []
  } catch (error) {
    console.error('加载句子失败', error)
    ElMessage.error('加载句子失败')
  } finally {
    loading.value = false
  }
}

// 生成提示词
const generatePrompts = async () => {
  if (!selectedChapterId.value || !selectedApiKey.value) {
    ElMessage.warning('请选择章节和API Key')
    return
  }
  
  generating.value = true
  try {
    // 调用新API - 使用正确的端点和请求格式
    const response = await api.post('/prompt/generate-prompts', {
      chapter_id: selectedChapterId.value,
      api_key_id: selectedApiKey.value,
      style: selectedStyle.value
    })
    
    if (response.success) {
      ElMessage.success(response.message)
      dialogVisible.value = false // 关闭对话框
      await loadChapters() // 重新加载章节列表以显示更新后的状态
      await loadSentences() // 重新加载以显示生成的Prompt
    }
  } catch (error) {
    console.error('生成失败', error)
    ElMessage.error('生成失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    generating.value = false
  }
}

onMounted(() => {
  loadChapters()
  loadApiKeys()
})
</script>

<style scoped>
.director-mode {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toolbar {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  background: #fff;
  padding: 20px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.sentence-item {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.sentence-header {
  margin-bottom: 10px;
  font-size: 16px;
  line-height: 1.5;
}

.index {
  color: #909399;
  margin-right: 10px;
  font-weight: bold;
}

.prompt-editor {
  background: #fafafa;
  padding: 15px;
  border-radius: 4px;
}

.label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 5px;
  font-weight: bold;
}
</style>
