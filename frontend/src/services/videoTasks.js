import api from './api'

export const videoTasksAPI = {
    // 获取视频任务列表
    list(params) {
        return api.get('/video-tasks/', { params })
    },

    // 获取单个视频任务详情
    getById(id) {
        return api.get(`/video-tasks/${id}`)
    },

    // 创建视频任务
    create(data) {
        return api.post('/video-tasks/', data)
    },

    // 删除视频任务
    delete(id) {
        return api.delete(`/video-tasks/${id}`)
    },

    // 重试失败的任务
    retry(id) {
        return api.post(`/video-tasks/${id}/retry`)
    },

    // 获取任务统计信息
    getStats() {
        return api.get('/video-tasks/stats')
    }
}
