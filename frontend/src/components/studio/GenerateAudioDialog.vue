<template>
  <el-dialog
    v-model="dialogVisible"
    title="生成音频"
    width="500px"
  >
    <el-form :inline="false" class="dialog-form" label-width="80px">
      <el-form-item label="API Key">
        <el-select v-model="selectedApiKey" placeholder="选择API Key" style="width: 100%">
          <el-option
            v-for="key in apiKeys"
            :key="key.id"
            :label="`${key.name} (${key.provider})`"
            :value="key.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="语音风格">
        <el-select v-model="voice" placeholder="选择语音风格" style="width: 100%">
          <el-option label="Alloy (通用)" value="alloy" />
          <el-option label="Echo (男声)" value="echo" />
          <el-option label="Fable (男声)" value="fable" />
          <el-option label="Onyx (深沉男声)" value="onyx" />
          <el-option label="Nova (女声)" value="nova" />
          <el-option label="Shimmer (清脆女声)" value="shimmer" />
        </el-select>
      </el-form-item>

      <el-form-item label="模型">
        <el-select v-model="model" placeholder="选择模型" style="width: 100%">
          <el-option label="TTS-1 (标准)" value="tts-1" />
          <el-option label="TTS-1-HD (高清)" value="tts-1-hd" />
        </el-select>
      </el-form-item>

      <div class="info-text">
        即将为 {{ sentencesCount }} 个句子生成音频。
      </div>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleGenerate">
          生成
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, defineProps, defineEmits, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import audioService from '@/services/audio'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  sentencesIds: {
    type: [Array, String],
    required: true
  },
  apiKeys: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:visible', 'generate-success'])

const dialogVisible = ref(props.visible)
const selectedApiKey = ref('')
const voice = ref('alloy')
const model = ref('tts-1')
const generating = ref(false)

const sentencesCount = computed(() => {
  return Array.isArray(props.sentencesIds) ? props.sentencesIds.length : 1
})

// 监听visible prop变化，更新dialogVisible
watch(() => props.visible, (newValue) => {
  dialogVisible.value = newValue
})

// 监听dialogVisible变化，通知父组件
watch(dialogVisible, (newValue) => {
  emit('update:visible', newValue)
})

// 更新visible状态并通知父组件
const updateDialogVisible = (newValue) => {
  dialogVisible.value = newValue
}

// 处理取消
const handleCancel = () => {
  updateDialogVisible(false)
  resetForm()
}

// 重置表单
const resetForm = () => {
  selectedApiKey.value = ''
  voice.value = 'alloy'
  model.value = 'tts-1'
}

// 处理生成音频
const handleGenerate = async () => {
  if (!selectedApiKey.value) {
    ElMessage.warning('请选择API Key')
    return
  }
  
  generating.value = true
  try {
    const ids = Array.isArray(props.sentencesIds) ? props.sentencesIds : [props.sentencesIds]
    const response = await audioService.generateAudio({
      sentences_ids: ids,
      api_key_id: selectedApiKey.value,
      voice: voice.value,
      model: model.value
    })
    
    if (response.success) {
      ElMessage.success(response.message)
      updateDialogVisible(false)
      emit('generate-success', response.task_id)
      // resetForm() // 成功后不重置，方便下次使用相同配置
    }
  } catch (error) {
    console.error('生成音频失败', error)
    ElMessage.error('生成音频失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.dialog-form {
  margin-bottom: 0;
}

.info-text {
  margin-top: 10px;
  color: #909399;
  font-size: 14px;
  text-align: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}
</style>
