<template>
  <Transition name="overlay-fade">
    <div v-if="visible" class="canvas-generating-overlay">
      <div class="shimmer-sweep"></div>
      <div class="overlay-content">
        <div class="pulse-dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
        <div class="overlay-label">{{ label }}</div>
        <div class="progress-track">
          <div class="progress-bar-fill">
            <div class="progress-shine"></div>
          </div>
        </div>
        <div class="overlay-hint">{{ hint }}</div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  label: { type: String, default: 'AI 正在生成...' },
  hint: { type: String, default: '正在处理中，请耐心等待' }
})
</script>

<style scoped>
.overlay-fade-enter-active {
  animation: overlay-in 0.35s ease both;
}

.overlay-fade-leave-active {
  animation: overlay-in 0.25s ease reverse both;
}

@keyframes overlay-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.canvas-generating-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(14px);
  border-radius: inherit;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.shimmer-sweep {
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 35%, rgba(75, 120, 255, 0.1) 50%, transparent 65%);
  transform: translateX(-100%) skewX(-8deg);
  animation: shimmer-sweep 2.4s ease-in-out infinite;
}

@keyframes shimmer-sweep {
  0% { transform: translateX(-120%) skewX(-8deg); }
  100% { transform: translateX(220%) skewX(-8deg); }
}

.overlay-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 0 28px;
  width: 100%;
  max-width: 320px;
}

.pulse-dots {
  display: flex;
  align-items: center;
  gap: 7px;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(75, 120, 255, 0.9);
  animation: pulse-dot 1.4s ease-in-out infinite;
}

.dot:nth-child(2) { animation-delay: 0.18s; }
.dot:nth-child(3) { animation-delay: 0.36s; }

@keyframes pulse-dot {
  0%, 100% { opacity: 0.28; transform: scale(0.75) translateY(0); }
  50% { opacity: 1; transform: scale(1.2) translateY(-3px); }
}

.overlay-label {
  font-size: 13px;
  font-weight: 600;
  color: #1f2a44;
  text-align: center;
}

.progress-track {
  width: 100%;
  height: 3px;
  border-radius: 999px;
  background: rgba(75, 120, 255, 0.14);
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  position: absolute;
  inset: 0;
  width: 60%;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent 0%, rgba(75, 120, 255, 0.24) 30%, rgba(75, 120, 255, 0.92) 50%, rgba(75, 120, 255, 0.24) 70%, transparent 100%);
  animation: progress-flow 1.8s ease-in-out infinite;
}

.progress-shine {
  position: absolute;
  top: 0;
  bottom: 0;
  right: 20%;
  width: 20%;
  border-radius: 999px;
  background: rgba(189, 211, 255, 0.9);
  filter: blur(1px);
}

@keyframes progress-flow {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(267%); }
}

.overlay-hint {
  font-size: 11px;
  color: #667085;
  text-align: center;
}
</style>
