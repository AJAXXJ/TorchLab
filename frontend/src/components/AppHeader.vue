<script setup lang="ts">
defineProps<{ generating: boolean }>()
const emit = defineEmits<{ (e: 'generate'): void; (e: 'clear'): void }>()
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
