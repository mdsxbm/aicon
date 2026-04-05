<template>
  <form class="assistant-composer" @submit.prevent="handleSubmit">
    <div class="assistant-composer__selectors">
      <label class="assistant-composer__field">
        <span class="assistant-composer__label">对话 Key</span>
        <select
          data-testid="assistant-api-key-select"
          class="assistant-composer__select"
          :value="selectedApiKeyId"
          :disabled="disabled || loading || apiKeysLoading || !apiKeyOptions.length"
          @change="handleApiKeyChange"
        >
          <option value="">请选择 API Key</option>
          <option
            v-for="option in apiKeyOptions"
            :key="option.id"
            :value="option.id"
          >
            {{ option.label }}{{ option.provider ? ` · ${option.provider}` : '' }}
          </option>
        </select>
      </label>

      <label class="assistant-composer__field">
        <span class="assistant-composer__label">对话模型</span>
        <select
          data-testid="assistant-chat-model-select"
          class="assistant-composer__select"
          :value="selectedChatModelId"
          :disabled="disabled || loading || chatModelsLoading || !chatModelOptions.length"
          @change="handleChatModelChange"
        >
          <option value="">请选择文本模型</option>
          <option
            v-for="modelId in chatModelOptions"
            :key="modelId"
            :value="modelId"
          >
            {{ modelId }}
          </option>
        </select>
      </label>
    </div>

    <textarea
      v-model="draft"
      class="assistant-composer__input"
      :placeholder="placeholder"
      :disabled="disabled"
      rows="4"
      @keydown="handleKeydown"
    ></textarea>

    <div class="assistant-composer__footer">
      <span class="assistant-composer__hint">Ctrl/⌘ + Enter 发送</span>
      <button
        class="assistant-composer__send"
        :class="{ 'assistant-composer__send--streaming': loading }"
        type="submit"
        :disabled="disabled || !draft.trim()"
      >
        {{ loading ? '处理中' : '发送' }}
      </button>
    </div>
  </form>
</template>

<script setup>
  import { ref, watch } from 'vue'

  const props = defineProps({
    // disabled: 外部控制当前是否允许继续发送，例如正在流式输出或等待确认。
    disabled: { type: Boolean, default: false },
    // loading: 发送后进入处理中态，用于更新按钮文案。
    loading: { type: Boolean, default: false },
    // placeholder: 根据当前选中节点和上下文动态提示用户怎么提问。
    placeholder: { type: String, default: '描述你想要的改动' },
    // apiKeyOptions: 可用于 assistant 对话的 API key 列表。
    apiKeyOptions: { type: Array, default: () => [] },
    // chatModelOptions: 当前 API key 对应的文本模型列表。
    chatModelOptions: { type: Array, default: () => [] },
    // selectedApiKeyId: 当前对话实际使用的 API key id。
    selectedApiKeyId: { type: String, default: '' },
    // selectedChatModelId: 当前对话实际使用的文本模型 id。
    selectedChatModelId: { type: String, default: '' },
    // apiKeysLoading: API key 列表是否仍在加载。
    apiKeysLoading: { type: Boolean, default: false },
    // chatModelsLoading: 文本模型列表是否仍在加载。
    chatModelsLoading: { type: Boolean, default: false }
  })

  const emit = defineEmits(['submit', 'update:selected-api-key-id', 'update:selected-chat-model-id'])

  const draft = ref('')
  const handleApiKeyChange = (event) => {
    /**
     * 把当前选择的 API key 往上抛给 composable。
     *
     * 参数说明：
     * - event: 原生 select change 事件。
     */
    emit('update:selected-api-key-id', event?.target?.value || '')
  }

  const handleChatModelChange = (event) => {
    /**
     * 把当前选择的文本模型往上抛给 composable。
     *
     * 参数说明：
     * - event: 原生 select change 事件。
     */
    emit('update:selected-chat-model-id', event?.target?.value || '')
  }

  const handleSubmit = () => {
    const text = draft.value.trim()
    if (!text || props.disabled) {
      return
    }

    emit('submit', text)
    draft.value = ''
  }

  // 输入框只管理当前这份草稿，其余会话状态全部放在 composable 里，
  // 这样 UI 层不会无意间变成第二套状态机。
  const handleKeydown = (event) => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault()
      handleSubmit()
    }
  }

  watch(
    () => props.disabled,
    (isDisabled) => {
      if (isDisabled) {
        draft.value = draft.value.trim()
      }
    }
  )
</script>

<style scoped>
  .assistant-composer {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 14px;
    border-radius: 22px;
    border: 1px solid rgba(34, 57, 98, 0.08);
    background: rgba(255, 255, 255, 0.94);
    box-shadow: 0 14px 32px rgba(34, 57, 98, 0.08);
  }

  .assistant-composer__selectors {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .assistant-composer__field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .assistant-composer__label {
    color: #51607d;
    font-size: 12px;
    font-weight: 600;
  }

  .assistant-composer__select {
    width: 100%;
    min-height: 40px;
    border: 1px solid rgba(34, 57, 98, 0.12);
    border-radius: 12px;
    padding: 0 12px;
    background: #fbfcff;
    color: #1f2a44;
    font: inherit;
    outline: none;
  }

  .assistant-composer__select:focus {
    border-color: rgba(75, 120, 255, 0.42);
    box-shadow: 0 0 0 3px rgba(75, 120, 255, 0.12);
  }

  .assistant-composer__select:disabled {
    background: #f3f6fb;
    color: #8a94a8;
  }

  .assistant-composer__input {
    width: 100%;
    min-height: 108px;
    resize: vertical;
    border: 1px solid rgba(34, 57, 98, 0.12);
    border-radius: 16px;
    padding: 12px 14px;
    background: #fbfcff;
    color: #1f2a44;
    font: inherit;
    line-height: 1.6;
    outline: none;
  }

  .assistant-composer__input:focus {
    border-color: rgba(75, 120, 255, 0.42);
    box-shadow: 0 0 0 3px rgba(75, 120, 255, 0.12);
  }

  .assistant-composer__input:disabled {
    background: #f3f6fb;
    color: #8a94a8;
  }

  .assistant-composer__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .assistant-composer__hint {
    color: #71809c;
    font-size: 12px;
  }

  .assistant-composer__send {
    padding: 10px 16px;
    border-radius: 999px;
    border: none;
    background: linear-gradient(180deg, #4b78ff, #355ce0);
    color: #fff;
    font-weight: 600;
    cursor: pointer;
  }

  .assistant-composer__send:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .assistant-composer__send--streaming:not(:disabled) {
    animation: pulse-stream 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    box-shadow: 0 0 0 0 rgba(75, 120, 255, 0.38);
  }

  @keyframes pulse-stream {
    0%,
    100% {
      transform: scale(1);
      box-shadow: 0 0 0 0 rgba(75, 120, 255, 0.38);
    }
    50% {
      transform: scale(0.98);
      box-shadow: 0 0 0 8px rgba(75, 120, 255, 0);
    }
  }
</style>
