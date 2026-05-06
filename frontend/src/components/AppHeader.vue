<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ generating: boolean }>()
const emit = defineEmits<{
  (e: 'generate'): void
  (e: 'clear'): void
  (e: 'load', json: string): void
  (e: 'save'): void
}>()

const fileInput = ref<HTMLInputElement>()

function onLoadClick() {
  fileInput.value?.click()
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => emit('load', reader.result as string)
  reader.readAsText(file)
  input.value = '' // 允许重复选同一文件
}
</script>

<template>
  <header
    class="flex items-center justify-between h-11 px-4 flex-shrink-0
           bg-[var(--color-surface-panel)] border-b border-[var(--color-border)]"
  >
    <span class="text-[15px] font-bold text-[#e0e0e0] tracking-wide">TorchLab</span>
    <div class="flex gap-2">
      <button
        class="px-3 py-1 text-[11px] font-semibold rounded
               bg-[#2a2a2a] text-[#aaa] hover:bg-[#3a3a3a]
               transition-colors cursor-pointer border-none"
        title="Save graph to file"
        @click="emit('save')"
      >
        Save
      </button>
      <button
        class="px-3 py-1 text-[11px] font-semibold rounded
               bg-[#2a2a2a] text-[#aaa] hover:bg-[#3a3a3a]
               transition-colors cursor-pointer border-none"
        title="Load graph from file"
        @click="onLoadClick"
      >
        Load
      </button>
      <input
        ref="fileInput"
        type="file" accept=".json"
        class="hidden"
        @change="onFileChange"
      />
      <button
        class="px-3 py-1 text-[11px] font-semibold rounded
               bg-[#2a2a2a] text-[#aaa] hover:bg-[#3a3a3a]
               transition-colors cursor-pointer border-none"
        @click="emit('clear')"
      >
        Clear
      </button>
      <button
        class="px-3 py-1 text-[11px] font-semibold rounded
               bg-[var(--color-accent-dim)] text-white
               hover:bg-[#388e3c] transition-colors
               cursor-pointer border-none
               disabled:opacity-40 disabled:cursor-not-allowed"
        :disabled="generating"
        @click="emit('generate')"
      >
        {{ generating ? 'Generating...' : 'Generate Code' }}
      </button>
    </div>
  </header>
</template>
