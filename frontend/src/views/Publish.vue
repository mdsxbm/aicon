<template>
  <div class="publish-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <el-icon class="title-icon"><Promotion /></el-icon>
          Bilibili发布管理
        </h1>
        <p class="page-description">将生成的视频发布到Bilibili平台</p>
      </div>
      <div class="header-right">
        <el-button @click="goToAccountManagement">
          <el-icon><User /></el-icon>
          账号管理
        </el-button>
        <el-button type="primary" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="publish-tabs">
      <!-- 可发布视频列表 -->
      <el-tab-pane label="可发布视频" name="videos">
        <div v-loading="videosLoading" class="videos-container">
          <el-empty v-if="!videosLoading && videos.length === 0" description="暂无可发布的视频">
            <el-button type="primary" @click="$router.push('/generation')">
              前往视频任务
            </el-button>
          </el-empty>

          <div v-else class="video-grid">
            <div v-for="video in videos" :key="video.id" class="video-card">
              <div class="video-preview">
                <video :src="video.video_url" controls class="video-player"></video>
              </div>
              <div class="video-info">
                <h3 class="video-title">{{ video.project_title }} - {{ video.chapter_title }}</h3>
                <div class="video-meta">
                  <span class="meta-item">
                    <el-icon><Clock /></el-icon>
                    {{ formatDuration(video.video_duration) }}
                  </span>
                  <span class="meta-item">
                    <el-icon><Calendar /></el-icon>
                    {{ formatDate(video.created_at) }}
                  </span>
                </div>
                <el-button type="primary" @click="handlePublish(video)" class="publish-btn">
                  <el-icon><Upload /></el-icon>
                  发布到B站
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 发布任务列表 -->
      <el-tab-pane label="发布任务" name="tasks">
        <div v-loading="tasksLoading" class="tasks-container">
          <el-empty v-if="!tasksLoading && tasks.length === 0" description="暂无发布任务" />

          <div v-else class="task-list">
            <div v-for="task in tasks" :key="task.id" class="task-item">
              <div class="task-header">
                <div class="header-left">
                  <h4 class="task-title">{{ task.title }}</h4>
                  <el-tag :type="getStatusType(task.status)">{{ getStatusText(task.status) }}</el-tag>
                </div>
                <el-button 
                  v-if="['failed', 'pending'].includes(task.status)" 
                  type="primary" 
                  link
                  :loading="retryingTaskId === task.id"
                  @click="handleRetry(task)"
                >
                  重试
                </el-button>
              </div>
              
              <el-progress 
                v-if="task.status === 'uploading'" 
                :percentage="task.progress" 
                :status="task.progress === 100 ? 'success' : undefined"
              />

              <div class="task-info">
                <span class="info-item">平台: {{ task.platform }}</span>
                <span class="info-item">创建时间: {{ formatDate(task.created_at) }}</span>
                <span v-if="task.bvid" class="info-item">
                  BV号: 
                  <a :href="`https://www.bilibili.com/video/${task.bvid}`" target="_blank" class="bv-link">
                    {{ task.bvid }}
                  </a>
                </span>
              </div>

              <el-alert v-if="task.error_message" :title="task.error_message" type="error" :closable="false" />
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 发布对话框 -->
    <el-dialog
      v-model="publishDialogVisible"
      title="发布到Bilibili"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="publishForm" :rules="publishRules" ref="publishFormRef" label-width="80px">
        <el-form-item label="发布账号" prop="account_id">
          <el-select v-model="publishForm.account_id" placeholder="请选择发布账号" style="width: 100%">
            <el-option
              v-for="acc in accounts"
              :key="acc.id"
              :label="acc.account_name + (acc.is_default ? ' (默认)' : '')"
              :value="acc.id"
              :disabled="!acc.cookie_valid"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input v-model="publishForm.title" maxlength="80" show-word-limit placeholder="请输入视频标题" />
        </el-form-item>

        <el-form-item label="简介" prop="desc">
          <el-input
            v-model="publishForm.desc"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
            placeholder="请输入视频简介"
          />
        </el-form-item>

        <el-form-item label="分区" prop="tid">
          <el-select v-model="publishForm.tid" placeholder="请选择分区" style="width: 100%">
            <el-option
              v-for="option in tidOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="封面" prop="cover_url">
          <el-upload
            class="cover-uploader"
            action="#"
            :show-file-list="false"
            :http-request="handleCoverUpload"
            :before-upload="beforeCoverUpload"
          >
            <div v-if="publishForm.cover_url" class="cover-preview">
              <img :src="getCoverUrl(publishForm.cover_url)" class="cover-image" />
              <div class="cover-actions" @click.stop>
                <el-button type="danger" circle size="small" @click="clearCover">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <el-icon v-else class="cover-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="form-tip">支持jpg/png格式，建议尺寸16:9，不传则使用视频默认封面</div>
        </el-form-item>

        <el-form-item label="标签" prop="tag">
          <el-input v-model="publishForm.tag" placeholder="多个标签用逗号分隔,最多10个" />
        </el-form-item>

        <el-form-item label="类型" prop="copyright">
          <el-radio-group v-model="publishForm.copyright">
            <el-radio :label="1">原创</el-radio>
            <el-radio :label="2">转载</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="publishForm.copyright === 2" label="转载源" prop="source">
          <el-input v-model="publishForm.source" placeholder="请输入转载来源" />
        </el-form-item>

        <el-form-item label="上传线路" prop="upload_line">
          <el-select v-model="publishForm.upload_line" style="width: 100%">
            <el-option label="百度云 (bda2)" value="bda2" />
            <el-option label="网宿 (ws)" value="ws" />
            <el-option label="腾讯云 (qn)" value="qn" />
            <el-option label="百度云SA (bldsa)" value="bldsa" />
            <el-option label="腾讯云 (tx)" value="tx" />
            <el-option label="腾讯云A (txa)" value="txa" />
            <el-option label="百度云 (bda)" value="bda" />
            <el-option label="阿里云 (alia)" value="alia" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPublish" :loading="publishing">
          确认发布
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Promotion, User, CircleCheck, Clock, Calendar, Upload, Refresh, Plus, Delete } from '@element-plus/icons-vue' // Added Plus, Delete
import bilibiliService from '@/services/bilibili'
import { uploadService } from '@/services/upload' // Import uploadService

const router = useRouter()
const activeTab = ref('videos')
const videos = ref([])
const tasks = ref([])
const accounts = ref([])
const videosLoading = ref(false)
const tasksLoading = ref(false)
const publishing = ref(false)
const publishDialogVisible = ref(false)
const publishFormRef = ref(null)
const tidOptions = ref([])
const currentVideo = ref(null)
const retryingTaskId = ref(null) // Added state
const coverPreviewUrl = ref('') // Added for cover preview

const publishForm = reactive({
  video_task_id: '',
  account_id: '',
  title: '',
  desc: '',
  tid: 171,
  tag: '',
  copyright: 1,
  source: '',
  cover_url: '', // Added cover_url
  upload_line: 'bda2',
  upload_limit: 3
})

const publishRules = {
  account_id: [{ required: true, message: '请选择发布账号', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  tid: [{ required: true, message: '请选择分区', trigger: 'change' }]
}


// 加载账号列表
const loadAccounts = async () => {
  try {
    accounts.value = await bilibiliService.getAccounts()
  } catch (error) {
    console.error('获取账号列表失败:', error)
  }
}

// 加载可发布视频
const loadVideos = async () => {
  videosLoading.value = true
  try {
    const res = await bilibiliService.getPublishableVideos()
    videos.value = res.videos || []
  } catch (error) {
    ElMessage.error('加载视频列表失败')
  } finally {
    videosLoading.value = false
  }
}

// 加载发布任务
const loadTasks = async () => {
  tasksLoading.value = true
  try {
    const res = await bilibiliService.getTasks()
    tasks.value = res || []
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  } finally {
    tasksLoading.value = false
  }
}

// 刷新所有数据
const handleRefresh = async () => {
  await Promise.all([loadVideos(), loadTasks()])
  ElMessage.success('刷新成功')
}

// 加载分区选项
const loadTidOptions = async () => {
  try {
    tidOptions.value = await bilibiliService.getTidOptions()
  } catch (error) {
    console.error('加载分区选项失败:', error)
  }
}

// 跳转到账号管理
const goToAccountManagement = () => {
  router.push('/bilibili-accounts')
}

// 打开发布对话框
const handlePublish = (video) => {
  if (accounts.value.length === 0) {
    ElMessage.warning('请先添加B站账号')
    goToAccountManagement()
    return
  }

  currentVideo.value = video
  publishForm.video_task_id = video.id
  publishForm.title = `${video.project_title} - ${video.chapter_title}`
  publishForm.desc = ''
  
  // 默认选中默认账号
  const defaultAccount = accounts.value.find(a => a.is_default && a.cookie_valid)
  // 如果没有默认账号，或者默认账号无效，则选第一个有效的
  const validAccount = defaultAccount || accounts.value.find(a => a.cookie_valid)
  publishForm.account_id = validAccount ? validAccount.id : ''
  
  publishDialogVisible.value = true
}

// 重试任务
const handleRetry = async (task) => {
  retryingTaskId.value = task.id
  try {
    const res = await bilibiliService.retryTask(task.id)
    if (res.success) {
      ElMessage.success('重试任务已提交')
      await loadTasks()
    } else {
      ElMessage.error(res.message || '重试失败')
    }
  } catch (error) {
    ElMessage.error('重试失败')
  } finally {
    retryingTaskId.value = null
  }
}

// 封面上传前检查
const beforeCoverUpload = (file) => {
  const isJPGOrPNG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt5M = file.size / 1024 / 1024 < 5

  if (!isJPGOrPNG) {
    ElMessage.error('封面图片只能是 JPG/PNG 格式!')
  }
  if (!isLt5M) {
    ElMessage.error('封面图片大小不能超过 5MB!')
  }
  return isJPGOrPNG && isLt5M
}

// 处理封面上传
const handleCoverUpload = async (options) => {
  const formData = new FormData()
  formData.append('file', options.file)
  
  // 生成本地预览
  coverPreviewUrl.value = URL.createObjectURL(options.file)
  
  try {
    const res = await uploadService.uploadFile({ formData })
    if (res.success) {
      // 保存对象键
      publishForm.cover_url = res.data.storage_key
      ElMessage.success('封面上传成功')
    } else {
      ElMessage.error('封面上传失败')
    }
  } catch (error) {
    ElMessage.error('封面上传失败')
    console.error(error)
  }
}

const getCoverUrl = (url) => {
  if (coverPreviewUrl.value) return coverPreviewUrl.value
  if (url && url.startsWith('http')) return url
  return '' // 无法预览对象键
}

// 清除封面
const clearCover = () => {
  publishForm.cover_url = ''
  coverPreviewUrl.value = ''
}

// 提交发布
const submitPublish = async () => {
  const valid = await publishFormRef.value.validate().catch(() => false)
  if (!valid) return

  publishing.value = true
  try {
    const res = await bilibiliService.publishVideo(publishForm)
    if (res.success) {
      ElMessage.success('发布任务已提交')
      publishDialogVisible.value = false
      activeTab.value = 'tasks'
      await loadTasks()
    } else {
      ElMessage.error(res.message || '发布失败')
    }
  } catch (error) {
    ElMessage.error('发布失败')
  } finally {
    publishing.value = false
  }
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    uploading: 'warning',
    published: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    pending: '等待中',
    uploading: '上传中',
    published: '已发布',
    failed: '失败'
  }
  return textMap[status] || status
}

onMounted(async () => {
  await Promise.all([
    loadAccounts(),
    loadVideos(),
    loadTasks(),
    loadTidOptions()
  ])
})
</script>

<style scoped>
.publish-management {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.title-icon {
  font-size: 32px;
  color: var(--primary-color);
}

.page-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.account-status-card {
  margin-bottom: 24px;
}

.account-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-icon {
  font-size: 24px;
}

.status-icon.success {
  color: var(--el-color-success);
}

.info-content {
  flex: 1;
}

.account-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.login-time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.publish-tabs {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.videos-container,
.tasks-container {
  min-height: 400px;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

.video-card {
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
}

.video-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.video-preview {
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-info {
  padding: 16px;
}

.video-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 13px;
  color: var(--text-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.publish-btn {
  width: 100%;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-item {
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  padding: 16px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.task-info {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-secondary);
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cover-uploader {
  border: 1px dashed var(--border-primary);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
  width: 178px;
  height: 100px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.cover-uploader:hover {
  border-color: var(--primary-color);
}

.cover-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 100px;
  text-align: center;
}

.cover-preview {
  width: 100%;
  height: 100%;
  position: relative;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cover-actions {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.cover-preview:hover .cover-actions {
  opacity: 1;
}

.form-tip {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-top: 4px;
}

.header-left .header-right {
  display: flex;
  gap: 12px;
}

.bv-link {
  color: var(--primary-color);
  text-decoration: none;
}

.bv-link:hover {
  text-decoration: underline;
}
</style>