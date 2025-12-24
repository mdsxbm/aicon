import api, { get, post, put } from './api'

export const movieService = {
    /**
     * 从章节提取场景（新架构）
     */
    extractScenes(chapterId, data) {
        return post(`/movie/chapters/${chapterId}/scenes`, data)
    },

    /**
     * 获取章节关联的剧本详情
     */
    getScript(chapterId) {
        return get(`/movie/chapters/${chapterId}/script`)
    },

    /**
     * 从剧本中提取角色
     */
    extractCharacters(scriptId, data) {
        return post(`/movie/scripts/${scriptId}/extract-characters`, data)
    },

    /**
     * 获取项目下的角色列表
     */
    getCharacters(projectId) {
        return get(`/movie/projects/${projectId}/characters`)
    },

    /**
     * 生成角色头像
     */
    generateCharacterAvatar(characterId, data) {
        return post(`/movie/characters/${characterId}/generate`, data)
    },

    /**
     * 批量生成角色定妆照
     */
    batchGenerateAvatars(projectId, data) {
        return post(`/movie/projects/${projectId}/characters/batch-generate`, data)
    },

    /**
     * 删除角色
     */
    deleteCharacter(characterId) {
        return api.delete(`/movie/characters/${characterId}`)
    },

    /**
     * 从剧本提取分镜
     */
    extractShots(scriptId, data) {
        return post(`/movie/scripts/${scriptId}/extract-shots`, data)
    },

    /**
     * 为剧本批量生成分镜关键帧
     */
    generateKeyframes(scriptId, data) {
        return post(`/movie/scripts/${scriptId}/generate-keyframes`, data)
    },

    /**
     * 创建过渡视频记录
     */
    createTransitions(scriptId, data) {
        return post(`/movie/scripts/${scriptId}/create-transitions`, data)
    },

    /**
     * 批量生成过渡视频
     */
    generateTransitionVideos(scriptId, data) {
        return post(`/movie/scripts/${scriptId}/generate-transition-videos`, data)
    },

    /**
     * 生成单个过渡视频
     */
    generateSingleTransition(transitionId, data) {
        return post(`/movie/transitions/${transitionId}/generate-video`, data)
    },

    /**
     * 更新分镜信息
     */
    updateShot(shotId, data) {
        return put(`/movie/shots/${shotId}`, data)
    }
}

export default movieService
