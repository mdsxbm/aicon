import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useTaskPoller } from './useTaskPoller'

export function useCharacterWorkflow(projectId, db) {
    const characters = ref([])
    const extracting = ref(false)
    const generatingAvatarId = ref(null)

    const loadCharacters = async () => {
        if (!projectId.value) return
        try {
            const response = await db.get(`/movie/projects/${projectId.value}/characters`)
            characters.value = response.data || []
        } catch (error) {
            console.error('Failed to load characters:', error)
        }
    }

    const extractCharacters = async (scriptId, apiKeyId, model) => {
        extracting.value = true
        try {
            const response = await db.post(`/movie/scripts/${scriptId}/extract-characters`, {
                api_key_id: apiKeyId,
                model
            })

            if (response.data.task_id) {
                ElMessage.success('角色提取任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.data.task_id, async () => {
                    ElMessage.success('角色提取完成')
                    await loadCharacters()
                    extracting.value = false
                }, (error) => {
                    ElMessage.error(`提取失败: ${error.message}`)
                    extracting.value = false
                })
            }
        } catch (error) {
            ElMessage.error('角色提取失败')
            extracting.value = false
        }
    }

    const generateAvatar = async (characterId, apiKeyId, model, prompt, style) => {
        generatingAvatarId.value = characterId
        try {
            const response = await db.post(`/movie/characters/${characterId}/generate`, {
                api_key_id: apiKeyId,
                model,
                prompt,
                style
            })

            if (response.data.task_id) {
                ElMessage.success('角色形象生成任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.data.task_id, async () => {
                    ElMessage.success('角色形象生成成功')
                    await loadCharacters()
                    generatingAvatarId.value = null
                }, (error) => {
                    ElMessage.error(`生成失败: ${error.message}`)
                    generatingAvatarId.value = null
                })
            }
        } catch (error) {
            ElMessage.error('无法启动形象生成')
            generatingAvatarId.value = null
        }
    }

    const batchGenerateAvatars = async (apiKeyId, model) => {
        try {
            const response = await db.post(`/movie/projects/${projectId.value}/characters/batch-generate`, {
                api_key_id: apiKeyId,
                model
            })

            if (response.data.task_id) {
                ElMessage.success('批量生成任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.data.task_id, async (result) => {
                    ElMessage.success(`批量生成完成: 成功 ${result.success}, 失败 ${result.failed}`)
                    await loadCharacters()
                }, (error) => {
                    ElMessage.error(`批量生成失败: ${error.message}`)
                })
            }
        } catch (error) {
            ElMessage.error('无法启动批量生成')
        }
    }

    const deleteCharacter = async (characterId) => {
        try {
            await db.delete(`/movie/characters/${characterId}`)
            ElMessage.success('角色已删除')
            await loadCharacters()
        } catch (error) {
            ElMessage.error('删除失败')
        }
    }

    return {
        characters,
        extracting,
        generatingAvatarId,
        loadCharacters,
        extractCharacters,
        generateAvatar,
        batchGenerateAvatars,
        deleteCharacter
    }
}
