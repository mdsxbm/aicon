import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useTaskPoller } from './useTaskPoller'

export function useSceneWorkflow(db) {
    const script = ref(null)
    const extracting = ref(false)

    const loadScript = async (chapterId) => {
        if (!chapterId) return
        try {
            const response = await db.get(`/movie/chapters/${chapterId}/script`)
            script.value = response.data
        } catch (error) {
            console.error('Failed to load script:', error)
            script.value = null
        }
    }

    const extractScenes = async (chapterId, apiKeyId, model) => {
        extracting.value = true
        try {
            const response = await db.post(`/movie/chapters/${chapterId}/scenes`, {
                api_key_id: apiKeyId,
                model
            })

            if (response.data.task_id) {
                ElMessage.success('场景提取任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.data.task_id, async () => {
                    ElMessage.success('场景提取完成')
                    await loadScript(chapterId)
                    extracting.value = false
                }, (error) => {
                    ElMessage.error(`提取失败: ${error.message}`)
                    extracting.value = false
                })
            }
        } catch (error) {
            ElMessage.error('场景提取失败')
            extracting.value = false
        }
    }

    return {
        script,
        extracting,
        loadScript,
        extractScenes
    }
}
