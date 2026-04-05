<template>
  <article class="assistant-tool">
    <div class="assistant-tool__header">
      <div>
        <div class="assistant-tool__eyebrow">{{ eyebrowText }}</div>
        <h3 class="assistant-tool__title">{{ titleText }}</h3>
      </div>
      <span class="assistant-tool__status" :class="`assistant-tool__status--${activity.status || 'completed'}`">
        {{ statusLabel }}
      </span>
    </div>

    <p v-if="summaryText" class="assistant-tool__summary">{{ summaryText }}</p>

    <div class="assistant-tool__grid">
      <details class="assistant-tool__details">
        <summary>{{ detailTitle }}</summary>
        <pre v-if="activity.args !== null && activity.args !== undefined">{{ formatJson(activity.args) }}</pre>
        <pre v-if="activity.result !== null && activity.result !== undefined">{{ formatJson(activity.result) }}</pre>
      </details>
    </div>
  </article>
</template>

<script setup>
  import { computed } from 'vue'

  const props = defineProps({
    activity: {
      type: Object,
      default: () => ({
        activityType: 'tool',
        title: '',
        toolName: '',
        status: 'completed',
        args: null,
        result: null
      })
    }
  })

  const statusLabelMap = {
    running: '运行中',
    pending: '排队中',
    failed: '失败',
    completed: '已完成'
  }

  const statusLabel = computed(
    () => statusLabelMap[String(props.activity.status || 'completed').trim()] || '已完成'
  )
  const eyebrowText = computed(() =>
    props.activity.activityType === 'step' ? 'Step' : 'Tool'
  )
  const titleText = computed(() =>
    props.activity.activityType === 'step'
      ? props.activity.title || 'agent_step'
      : props.activity.toolName || 'unknown_tool'
  )
  const summaryText = computed(() =>
    props.activity.activityType === 'step'
      ? `${titleText.value} · ${statusLabel.value}`
      : ''
  )
  const detailTitle = computed(() =>
    props.activity.activityType === 'step' ? titleText.value : (props.activity.toolName || 'unknown_tool')
  )

  const formatJson = (value) => {
    // 这里保留格式化 JSON，方便学习工具输入输出结构。
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return String(value || '')
    }
  }
</script>

<style scoped>
  .assistant-tool {
    padding: 14px 16px;
    border-radius: 18px;
    border: 1px solid rgba(34, 57, 98, 0.08);
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 10px 24px rgba(34, 57, 98, 0.06);
  }

  .assistant-tool__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }

  .assistant-tool__eyebrow {
    color: #6a768f;
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .assistant-tool__title {
    margin: 4px 0 0;
    color: #1f2a44;
    font-size: 15px;
    line-height: 1.35;
  }

  .assistant-tool__status {
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
  }

  .assistant-tool__status--completed {
    background: #e8f3eb;
    color: #0f6a36;
  }

  .assistant-tool__status--running,
  .assistant-tool__status--pending {
    background: #fff3d6;
    color: #b06000;
  }

  .assistant-tool__status--failed {
    background: #fce8e6;
    color: #b42318;
  }

  .assistant-tool__summary {
    margin: 10px 0 0;
    color: #52607a;
    font-size: 13px;
    line-height: 1.6;
  }

  .assistant-tool__grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 10px;
  }

  .assistant-tool__details {
    color: #52607a;
    font-size: 12px;
  }

  .assistant-tool__details summary {
    cursor: pointer;
    color: #355ce0;
  }

  .assistant-tool__details pre {
    margin: 8px 0 0;
    padding: 12px;
    overflow: auto;
    border-radius: 14px;
    background: rgba(34, 57, 98, 0.04);
    white-space: pre-wrap;
  }
</style>
