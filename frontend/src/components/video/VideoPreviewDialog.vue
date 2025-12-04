<template>
  <el-dialog
    :title="title || '视频预览'"
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    width="800px"
    destroy-on-close
    append-to-body
  >
    <div class="preview-container">
      <video 
        controls 
        autoplay
        class="video-player"
        :src="videoUrl"
      >
        您的浏览器不支持视频播放
      </video>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
        <el-button type="primary" @click="downloadVideo">
          <el-icon><Download /></el-icon> 下载
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { Download } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: Boolean,
  videoUrl: String,
  title: String
})

defineEmits(['update:modelValue'])

const downloadVideo = () => {
  if (props.videoUrl) {
    const a = document.createElement('a')
    a.href = props.videoUrl
    a.download = `video_${props.title || 'generated'}.mp4`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }
}
</script>

<style scoped>
.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  background: #000;
  border-radius: 4px;
  overflow: hidden;
  min-height: 300px;
  max-height: 60vh;
}

.video-player {
  max-width: 100%;
  max-height: 60vh;
}
</style>
