<template>
  <div class="movie-studio-layout">
    <!-- 侧边栏：章节选择 -->
    <div class="studio-sidebar-left">
      <ChapterSelector 
        v-model="selectedChapterId" 
        :project-id="projectId"
      />
    </div>

    <!-- 主体内容区 -->
    <div class="studio-main">
      <!-- 顶部导航 -->
      <div class="studio-header">
        <el-button icon="ArrowLeft" @click="goBack">返回</el-button>
        <h2>电影工作室</h2>
      </div>

      <!-- 工作流步骤指示器 -->
      <WorkflowStepper :current-step="currentStep" />

      <!-- 内容区 -->
      <div class="studio-body" v-loading="loading">
        <div v-if="!selectedChapterId" class="empty-selection">
          <el-empty description="请从左侧选择一个章节开始制作" />
        </div>

        <div v-else class="workflow-content">
          <!-- 步骤0: 角色管理 -->
          <CharacterPanel
            v-show="currentStep === 0"
            :characters="characterWorkflow.characters.value"
            :extracting="characterWorkflow.extracting.value"
            :generating-id="characterWorkflow.generatingAvatarId.value"
            :can-extract="!!sceneWorkflow.script.value"
            @extract-characters="handleExtractCharacters"
            @generate-avatar="handleGenerateAvatar"
            @delete-character="handleDeleteCharacter"
            @batch-generate="handleBatchGenerateAvatars"
          />

          <!-- 步骤1: 场景提取 -->
          <ScenePanel
            v-show="currentStep === 1"
            :scenes="sceneWorkflow.script.value?.scenes || []"
            :extracting="sceneWorkflow.extracting.value"
            :can-extract="canExtractScenes"
            @extract-scenes="handleExtractScenes"
          />

          <!-- 步骤2: 分镜提取 -->
          <ShotPanel
            v-show="currentStep === 2"
            :shots="shotWorkflow.allShots.value"
            :extracting="shotWorkflow.extracting.value"
            :can-extract="canExtractShots"
            @extract-shots="handleExtractShots"
          />

          <!-- 步骤3: 关键帧生成 -->
          <KeyframePanel
            v-show="currentStep === 3"
            :shots="shotWorkflow.allShots.value"
            :generating="shotWorkflow.generatingKeyframes.value"
            :can-generate="canGenerateKeyframes"
            @generate-keyframes="handleGenerateKeyframes"
          />

          <!-- 步骤4: 过渡视频 -->
          <TransitionPanel
            v-show="currentStep === 4"
            :transitions="transitionWorkflow.transitions.value"
            :creating="transitionWorkflow.creating.value"
            :generating="transitionWorkflow.generating.value"
            :can-create="canCreateTransitions"
            :can-generate="canGenerateTransitionVideos"
            @create-transitions="handleCreateTransitions"
            @generate-videos="handleGenerateTransitionVideos"
          />

          <!-- 步骤5: 最终合成 -->
          <div v-show="currentStep === 5" class="final-panel">
            <el-result
              icon="success"
              title="准备完成"
              sub-title="所有素材已准备就绪，可以进行最终合成"
            >
              <template #extra>
                <el-button type="primary" size="large">
                  合成完整视频
                </el-button>
              </template>
            </el-result>
          </div>
        </div>
      </div>
    </div>

    <!-- 配置对话框 -->
    <StudioDialogs
      v-model:visible="showDialog"
      v-model:genConfig="genConfig"
      :mode="dialogMode"
      :api-keys="apiKeys"
      :loading="dialogLoading"
      @confirm="handleDialogConfirm"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useMovieWorkflow } from '@/composables/useMovieWorkflow'
import { apiKeysService } from '@/services/apiKeys'
import ChapterSelector from '@/components/studio/ChapterSelector.vue'
import WorkflowStepper from '@/components/studio/WorkflowStepper.vue'
import CharacterPanel from '@/components/studio/CharacterPanel.vue'
import ScenePanel from '@/components/studio/ScenePanel.vue'
import ShotPanel from '@/components/studio/ShotPanel.vue'
import KeyframePanel from '@/components/studio/KeyframePanel.vue'
import TransitionPanel from '@/components/studio/TransitionPanel.vue'
import StudioDialogs from '@/components/studio/StudioDialogs.vue'

const {
  selectedChapterId,
  projectId,
  currentStep,
  loading,
  characterWorkflow,
  sceneWorkflow,
  shotWorkflow,
  transitionWorkflow,
  canExtractScenes,
  canExtractShots,
  canGenerateKeyframes,
  canCreateTransitions,
  canGenerateTransitionVideos,
  goBack
} = useMovieWorkflow()

// Dialog state
const showDialog = ref(false)
const dialogMode = ref('character')
const dialogLoading = ref(false)
const apiKeys = ref([])
const genConfig = ref({
  api_key_id: '',
  model: '',
  style: 'cinematic',
  prompt: ''
})

// Load API keys
const loadApiKeys = async () => {
  try {
    const keys = await apiKeysService.getAPIKeys()
    apiKeys.value = keys.api_keys || []
  } catch (error) {
    console.error('Failed to load API keys:', error)
  }
}

loadApiKeys()

// Handlers
const handleExtractCharacters = () => {
  dialogMode.value = 'character'
  showDialog.value = true
}

const handleGenerateAvatar = (char) => {
  // TODO: Implement avatar generation dialog
  console.log('Generate avatar for:', char)
}

const handleDeleteCharacter = async (char) => {
  await characterWorkflow.deleteCharacter(char.id)
}

const handleBatchGenerateAvatars = () => {
  dialogMode.value = 'batch-avatars'
  showDialog.value = true
}

const handleExtractScenes = () => {
  dialogMode.value = 'scenes'
  showDialog.value = true
}

const handleExtractShots = () => {
  dialogMode.value = 'shots'
  showDialog.value = true
}

const handleGenerateKeyframes = () => {
  dialogMode.value = 'keyframes'
  showDialog.value = true
}

const handleCreateTransitions = () => {
  dialogMode.value = 'transitions'
  showDialog.value = true
}

const handleGenerateTransitionVideos = () => {
  dialogMode.value = 'transition-videos'
  showDialog.value = true
}

const handleDialogConfirm = async () => {
  const { api_key_id, model } = genConfig.value
  
  if (!api_key_id) {
    return
  }

  showDialog.value = false

  if (dialogMode.value === 'character') {
    await characterWorkflow.extractCharacters(sceneWorkflow.script.value.id, api_key_id, model)
  } else if (dialogMode.value === 'scenes') {
    await sceneWorkflow.extractScenes(selectedChapterId.value, api_key_id, model)
  } else if (dialogMode.value === 'shots') {
    await shotWorkflow.extractShots(sceneWorkflow.script.value.id, api_key_id, model)
  } else if (dialogMode.value === 'keyframes') {
    await shotWorkflow.generateKeyframes(sceneWorkflow.script.value.id, api_key_id, model)
  } else if (dialogMode.value === 'transitions') {
    await transitionWorkflow.createTransitions(sceneWorkflow.script.value.id, api_key_id, model)
  } else if (dialogMode.value === 'transition-videos') {
    await transitionWorkflow.generateTransitionVideos(sceneWorkflow.script.value.id, api_key_id, 'veo_3_1-fast')
  } else if (dialogMode.value === 'batch-avatars') {
    await characterWorkflow.batchGenerateAvatars(api_key_id, model)
  }
}
</script>

<style scoped>
.movie-studio-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.studio-sidebar-left {
  width: 250px;
  flex-shrink: 0;
  height: 100%;
}

.studio-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #f5f7fa;
}

.studio-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.studio-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.studio-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.empty-selection {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.workflow-content {
  max-width: 1400px;
  margin: 0 auto;
}

.final-panel {
  background: white;
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
