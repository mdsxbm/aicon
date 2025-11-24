<template>
  <div class="director-mode">
    <div class="toolbar">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="选择章节">
          <el-select v-model="selectedChapterId" placeholder="请选择章节" @change="loadSentences">
            <el-option
              v-for="chapter in chapters"
              :key="chapter.id"
              :label="chapter.title"
              :value="chapter.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="API Key">
          <el-select v-model="selectedApiKey" placeholder="选择API Key">
            <el-option
              v-for="key in apiKeys"
              :key="key.id"
              :label="key.name + ' (' + key.provider + ')'"
              :value="key.key"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="风格">
          <el-select v-model="selectedStyle" placeholder="选择风格">
            <el-option label="电影质感 (Cinematic)" value="cinematic" />
            <el-option label="二次元 (Anime)" value="anime" />
            <el-option label="插画 (Illustration)" value="illustration" />
            <el-option label="水墨 (Ink)" value="ink" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" :loading="generating" @click="generatePrompts">
            生成分镜脚本
          </el-button>
        </el-form-item>
      </el-form>
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
            <div class="label">AI Prompt:</div>
            <el-input
              v-model="sentence.edited_prompt"
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
import { ElMessage } from 'element-plus'
import chaptersService from '@/services/chapters'
import paragraphsService from '@/services/paragraphs'
import sentencesService from '@/services/sentences'
import axios from 'axios'

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

// 加载章节
const loadChapters = async () => {
  try {
    const res = await chaptersService.getChapters(props.projectId)
    chapters.value = res.chapters || []
  } catch (error) {
    console.error('加载章节失败', error)
  }
}

// 加载API Keys (模拟，实际应从API获取)
const loadApiKeys = async () => {
  // TODO: 调用真实的API Key列表接口
  // 这里暂时硬编码用于演示，或者从localStorage读取
  apiKeys.value = [
    { id: '1', name: 'My Volcengine', provider: 'volcengine', key: 'sk-placeholder' },
    { id: '2', name: 'My DeepSeek', provider: 'deepseek', key: 'sk-placeholder' }
  ]
}

// 加载句子
const loadSentences = async () => {
  if (!selectedChapterId.value) return
  
  loading.value = true
  try {
    // 获取该章节下的所有段落
    const paragraphsRes = await paragraphsService.getParagraphs(selectedChapterId.value)
    const paragraphs = paragraphsRes.paragraphs || []
    
    // 获取所有段落的句子
    let allSentences = []
    for (const p of paragraphs) {
      const sentencesRes = await sentencesService.getSentences(p.id)
      const paragraphSentences = sentencesRes.sentences || []
      allSentences = allSentences.concat(paragraphSentences)
    }
    
    sentences.value = allSentences.sort((a, b) => a.order_index - b.order_index)
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
    const response = await axios.post('/api/v1/prompt/generate-prompts', {
      chapter_id: selectedChapterId.value,
      api_key: selectedApiKey.value,
      provider: 'volcengine', // 暂时硬编码，应从selectedApiKey中获取
      style: selectedStyle.value
    })
    
    if (response.data.success) {
      ElMessage.success(response.data.message)
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
