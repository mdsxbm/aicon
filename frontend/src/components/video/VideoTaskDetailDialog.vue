<template>
  <el-dialog
    title="任务详情"
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    width="700px"
    destroy-on-close
  >
    <div v-loading="loading" class="detail-container">
      <template v-if="task">
        <!-- 基本信息 -->
        <div class="info-section">
          <div class="info-row">
            <span class="label">项目：</span>
            <span class="value">{{ task.project_title }}</span>
          </div>
          <div class="info-row">
            <span class="label">章节：</span>
            <span class="value">{{ task.chapter_title }}</span>
          </div>
          <div class="info-row">
            <span class="label">创建时间：</span>
            <span class="value">{{ formatDate(task.created_at) }}</span>
          </div>
          <div class="info-row">
            <span class="label">状态：</span>
            <el-tag :type="getStatusType(task.status)">
              {{ getStatusText(task.status) }}
            </el-tag>
          </div>
        </div>

        <!-- 进度条 -->
        <div class="progress-section">
          <div class="progress-header">
            <span>处理进度</span>
            <span class="percentage">{{ task.progress }}%</span>
          </div>
          <el-progress 
            :percentage="task.progress" 
            :status="task.status === 'failed' ? 'exception' : (task.status === 'completed' ? 'success' : '')"
            :show-text="false"
            :stroke-width="10"
          />
          <div class="progress-steps">
            <el-steps :active="getActiveStep(task.status)" finish-status="success" align-center>
              <el-step title="准备" description="验证素材" />
              <el-step title="字幕" description="生成字幕" />
              <el-step title="合成" description="视频合成" />
              <el-step title="完成" description="上传结果" />
            </el-steps>
          </div>
          <div class="current-action" v-if="task.status !== 'completed' && task.status !== 'failed'">
            <el-icon class="is-loading"><Loading /></el-icon>
            {{ getProgressText(task) }}
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-if="task.status === 'failed'" class="error-section">
          <el-alert
            title="任务失败"
            type="error"
            :description="task.error_message"
            show-icon
            :closable="false"
          />
        </div>

        <!-- 视频预览 -->
        <div v-if="task.status === 'completed' && task.video_url" class="video-section">
          <div class="video-header">
            <span>生成结果</span>
            <div class="video-actions">
              <el-button type="primary" link @click="downloadVideo">
                <el-icon><Download /></el-icon> 下载视频
              </el-button>
            </div>
          </div>
          <div class="video-player-container">
            <video 
              controls 
              class="video-player"
              :src="task.video_url"
            >
              您的浏览器不支持视频播放
            </video>
          </div>
          <div class="video-info" v-if="task.video_duration">
            时长: {{ formatDuration(task.video_duration) }}
          </div>
        </div>

        <!-- 生成设置 -->
        <div class="settings-section">
          <el-collapse>
            <el-collapse-item title="生成参数配置" name="1">
              <pre class="json-viewer">{{ JSON.stringify(getGenSetting(task), null, 2) }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>
      </template>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useVideoTasks } from '@/composables/useVideoTasks'
import { formatDate } from '@/utils/dateUtils'
import { Loading, Download } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: Boolean,
  taskId: String
})

const emit = defineEmits(['update:modelValue'])

const { fetchTaskById } = useVideoTasks()
const loading = ref(false)
const task = ref(null)

watch(() => props.modelValue, async (val) => {
  if (val && props.taskId) {
    loading.value = true
    try {
      task.value = await fetchTaskById(props.taskId)
    } catch (error) {
      console.error('获取任务详情失败:', error)
    } finally {
      loading.value = false
    }
  } else {
    task.value = null
  }
})

// 辅助函数
const getStatusType = (status) => {
  const map = {
    pending: 'info',
    validating: 'primary',
    downloading_materials: 'primary',
    generating_subtitles: 'primary',
    synthesizing_videos: 'warning',
    concatenating: 'warning',
    uploading: 'primary',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending: '等待中',
    validating: '验证素材',
    downloading_materials: '下载素材',
    generating_subtitles: '生成字幕',
    synthesizing_videos: '合成视频',
    concatenating: '拼接视频',
    uploading: '上传结果',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const getActiveStep = (status) => {
  if (status === 'completed') return 4
  if (status === 'failed') return 0 
  
  const steps = [
    ['pending', 'validating', 'downloading_materials'],
    ['generating_subtitles'],
    ['synthesizing_videos', 'concatenating'],
    ['uploading']
  ]
  
  for (let i = 0; i < steps.length; i++) {
    if (steps[i].includes(status)) return i
  }
  
  return 0
}

const getProgressText = (task) => {
  if (task.status === 'completed') return '已完成'
  if (task.status === 'failed') return '失败'
  
  if (task.current_sentence_index !== null && task.total_sentences) {
    return `正在处理第 ${task.current_sentence_index}/${task.total_sentences} 句`
  }
  return getStatusText(task.status)
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const getGenSetting = (task) => {
  if (!task || !task.gen_setting) return {}
  try {
    return typeof task.gen_setting === 'string' 
      ? JSON.parse(task.gen_setting) 
      : task.gen_setting
  } catch (e) {
    console.error('解析生成设置失败:', e)
    return {}
  }
}

const downloadVideo = () => {
  if (task.value && task.value.video_url) {
    const a = document.createElement('a')
    a.href = task.value.video_url
    a.download = `video_${task.value.chapter_title || 'generated'}.mp4`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }
}
</script>

<style scoped>
.detail-container {
  padding: 10px;
}

.info-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
  background: var(--bg-secondary);
  padding: 16px;
  border-radius: 8px;
}

.info-row {
  display: flex;
  align-items: center;
}

.label {
  color: var(--text-secondary);
  width: 80px;
}

.value {
  color: var(--text-primary);
  font-weight: 500;
}

.progress-section {
  margin-bottom: 24px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-weight: 500;
}

.progress-steps {
  margin-top: 24px;
}

.current-action {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--primary-color);
  font-size: 14px;
}

.error-section {
  margin-bottom: 24px;
}

.video-section {
  margin-bottom: 24px;
}

.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 500;
}

.video-player-container {
  width: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 16/9; /* 默认比例，实际会根据视频调整 */
  display: flex;
  justify-content: center;
  align-items: center;
}

.video-player {
  max-width: 100%;
  max-height: 400px;
}

.video-info {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  text-align: right;
}

.json-viewer {
  background: var(--bg-secondary);
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow: auto;
  max-height: 200px;
}
</style>
