import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import movieService from '@/services/movie'
import { useTaskPoller } from './useTaskPoller'

/**
 * 角色工作流管理
 * 遵循架构：使用movieService而非直接调用api
 */
export function useCharacterWorkflow(projectId) {
    const characters = ref([])
    const extracting = ref(false)
    const generatingIds = ref(new Set()) // 改用Set跟踪多个正在生成的角色
    const batchGenerating = ref(false) // 跟踪批量生成状态

    const loadCharacters = async () => {
        if (!projectId.value) return
        try {
            const response = await movieService.getCharacters(projectId.value)
            // 注意：response已经是data，不需要response.data
            characters.value = response.characters || []
        } catch (error) {
            console.error('Failed to load characters:', error)
        }
    }

    const extractCharacters = async (chapterId, apiKeyId, model) => {
        extracting.value = true
        try {
            const response = await movieService.extractCharacters(chapterId, {
                api_key_id: apiKeyId,
                model
            })

            if (response.task_id) {
                ElMessage.success('角色提取任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async () => {
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
        generatingIds.value.add(characterId) // 添加到Set
        try {
            const response = await movieService.generateCharacterAvatar(characterId, {
                api_key_id: apiKeyId,
                model,
                prompt,
                style
            })

            if (response.task_id) {
                ElMessage.success('角色形象生成任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async () => {
                    ElMessage.success('角色形象生成成功')
                    await loadCharacters()
                    generatingIds.value.delete(characterId) // 从Set中移除
                }, (error) => {
                    ElMessage.error(`生成失败: ${error.message}`)
                    generatingIds.value.delete(characterId) // 从Set中移除
                })
            }
        } catch (error) {
            ElMessage.error('无法启动形象生成')
            generatingIds.value.delete(characterId) // 从Set中移除
        }
    }

    const batchGenerateAvatars = async (apiKeyId, model) => {
        batchGenerating.value = true // 设置加载状态
        try {
            const response = await movieService.batchGenerateAvatars(projectId.value, {
                api_key_id: apiKeyId,
                model
            })

            if (response.task_id) {
                ElMessage.success('批量生成任务已提交')
                const { startPolling } = useTaskPoller()
                startPolling(response.task_id, async (result) => {
                    ElMessage.success(`批量生成完成: 成功 ${result.success}, 失败 ${result.failed}`)
                    await loadCharacters()
                    batchGenerating.value = false // 完成后重置状态
                }, (error) => {
                    ElMessage.error(`批量生成失败: ${error.message}`)
                    batchGenerating.value = false // 失败后重置状态
                })
            } else {
                batchGenerating.value = false // 没有task_id时重置状态
            }
        } catch (error) {
            ElMessage.error('无法启动批量生成')
            batchGenerating.value = false // 异常时重置状态
        }
    }

    const deleteCharacter = async (characterId) => {
        try {
            await movieService.deleteCharacter(characterId)
            ElMessage.success('角色已删除')
            await loadCharacters()
        } catch (error) {
            ElMessage.error('删除角色失败')
        }
    }

    return {
        characters,
        extracting,
        generatingIds, // 返回Set而不是单个ID
        batchGenerating, // 批量生成加载状态
        loadCharacters,
        extractCharacters,
        generateAvatar,
        batchGenerateAvatars,
        deleteCharacter
    }
}
