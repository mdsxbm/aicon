import api from './api';

export default {
    /**
     * 生成音频
     * @param {Object} data - 请求数据
     * @param {string} data.api_key_id - API Key ID
     * @param {Array<string>} data.sentences_ids - 句子ID列表
     * @param {string} [data.voice] - 语音风格
     * @param {string} [data.model] - 模型名称
     * @returns {Promise<Object>} 响应数据
     */
    generateAudio(data) {
        return api.post('/audio/generate-audio', data);
    }
};
