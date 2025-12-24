<template>
  <div class="workflow-stepper">
    <el-steps :active="activeStep" align-center finish-status="success">
      <el-step 
        v-for="(step, index) in steps" 
        :key="index"
        :title="step.title"
        :description="step.description"
        :icon="step.icon"
      />
    </el-steps>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentStep: {
    type: Number,
    default: 0
  }
})

const steps = [
  {
    title: '角色管理',
    description: '提取角色 + 生成形象',
    icon: 'User'
  },
  {
    title: '场景提取',
    description: '从章节提取场景',
    icon: 'Film'
  },
  {
    title: '分镜提取',
    description: '从场景提取分镜',
    icon: 'Camera'
  },
  {
    title: '关键帧生成',
    description: '生成分镜关键帧',
    icon: 'Picture'
  },
  {
    title: '过渡视频',
    description: '生成分镜过渡',
    icon: 'VideoCamera'
  },
  {
    title: '最终合成',
    description: '合成完整视频',
    icon: 'Finished'
  }
]

const activeStep = computed(() => props.currentStep)
</script>

<style scoped>
.workflow-stepper {
  padding: 20px;
  background: white;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

:deep(.el-step__title) {
  font-size: 14px;
  font-weight: 500;
}

:deep(.el-step__description) {
  font-size: 12px;
  color: #909399;
}
</style>
