<script setup lang="ts">
import { ref, watch } from 'vue'
import type { NodeMeta } from '@/types/nodes'

const props = defineProps<{
  grouped: Record<string, Array<{ type: string; meta: NodeMeta }>>
  loading: boolean
  error: string | null
}>()

const emit = defineEmits<{ (e: 'add-node', type: string): void }>()

// ── 面板整体折叠 ──
const isPanelOpen = ref(loadPanelOpen())
function loadPanelOpen(): boolean {
  try { return JSON.parse(localStorage.getItem('torchlab-palette-open') || 'true') }
  catch { return true }
}
watch(isPanelOpen, (v) => {
  localStorage.setItem('torchlab-palette-open', JSON.stringify(v))
})

// ── 分类折叠 ──
const collapsed = ref<Record<string, boolean>>(loadCollapsed())
function loadCollapsed(): Record<string, boolean> {
  try { return JSON.parse(localStorage.getItem('torchlab-palette-collapse') || '{}') }
  catch { return {} }
}
watch(collapsed, (v) => {
  localStorage.setItem('torchlab-palette-collapse', JSON.stringify(v))
}, { deep: true })

function toggleCat(cat: string) {
  collapsed.value[cat] = !collapsed.value[cat]
}

function catColor(cat: string): string {
  const m: Record<string, string> = {
    data: '#1a7a6b', layer: '#2c5aa0', activation: '#a0522c',
    control_flow: '#6b4090', custom: '#5a4080',
  }
  return m[cat] || '#555'
}

function onClick(type: string) { emit('add-node', type) }

function onDragStart(e: DragEvent, type: string) {
  if (e.dataTransfer) {
    e.dataTransfer.setData('application/torchlab-node', type)
    e.dataTransfer.effectAllowed = 'copy'
  }
}
</script>

<template>
  <div class="palette-overlay" :class="{ closed: !isPanelOpen }">
    <!-- Toggle tab — 始终可见 -->
    <button
      class="palette-toggle"
      :title="isPanelOpen ? 'Collapse panel' : 'Expand panel'"
      @click="isPanelOpen = !isPanelOpen"
    >
      <svg
        class="w-3 h-3 transition-transform duration-200"
        :class="{ 'rotate-180': !isPanelOpen }"
        viewBox="0 0 12 14" fill="currentColor"
      >
        <path d="M0 0l12 7-12 7V0z" />
      </svg>
    </button>

    <!-- Content -->
    <div class="palette-content">
      <div v-if="loading" class="p-3 text-[11px] text-[var(--color-text-subtle)]">Loading...</div>
      <div v-else-if="error" class="p-3 text-[11px] text-red-500">{{ error }}</div>

      <template v-else>
        <!-- Search (placeholder) -->
        <div class="p-2">
          <input
            type="text" placeholder="Search..."
            disabled
            class="w-full px-2 py-1.5 text-[11px] bg-[#222] border border-[#333]
                   rounded text-[#999] outline-none placeholder-[#444]"
          />
        </div>

        <div v-for="(items, cat) in grouped" :key="cat" class="flex flex-col">
          <!-- Category header -->
          <button
            class="flex items-center gap-1.5 px-2.5 py-1.5
                   text-[10px] uppercase text-[#666] hover:text-[#999]
                   tracking-[0.5px] cursor-pointer border-none bg-transparent
                   transition-colors text-left"
            @click="toggleCat(cat)"
          >
            <svg
              class="w-2.5 h-2.5 transition-transform duration-150 text-[#555]"
              :class="{ 'rotate-90': !collapsed[cat] }"
              viewBox="0 0 10 14" fill="currentColor"
            >
              <path d="M0 0l10 7-10 7V0z" />
            </svg>
            <span
              class="inline-block w-1.5 h-1.5 rounded-full flex-shrink-0"
              :style="{ background: catColor(cat) }"
            ></span>
            <span class="flex-1">{{ cat }}</span>
            <span class="text-[10px] text-[var(--color-text-subtle)]">{{ items.length }}</span>
          </button>

          <!-- Node items -->
          <div v-if="!collapsed[cat]" class="flex flex-col">
            <button
              v-for="{ type, meta } in items" :key="type"
              class="flex items-center gap-1.5 w-full px-2.5 py-1
                     text-[11px] text-[#bbb] hover:text-[#e0e0e0]
                     hover:bg-[var(--color-surface-hover)]
                     bg-transparent border-none cursor-grab
                     transition-colors text-left"
              draggable="true"
              :title="meta.description"
              @click="onClick(type)"
              @dragstart="onDragStart($event, type)"
            >
              <span
                class="inline-block w-1 h-1 rounded-full flex-shrink-0"
                :style="{ background: catColor(cat) }"
              ></span>
              <span class="flex-1 truncate">{{ meta.display_name }}</span>
              <span
                v-if="meta.is_custom"
                class="text-[9px] bg-[#333] text-[#888] px-1 rounded-sm font-bold"
              >+</span>
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.palette-overlay {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 200px;
  z-index: 20;
  transform: translateX(0);
  transition: transform 0.25s ease;
  display: flex;
}
.palette-overlay.closed {
  transform: translateX(-168px);
}

.palette-toggle {
  position: absolute;
  right: 0; top: 50%;
  transform: translateY(-50%);
  width: 32px; height: 64px;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-panel);
  border: 1px solid var(--color-border);
  border-left: none;
  border-radius: 0 6px 6px 0;
  color: #888;
  cursor: pointer;
  z-index: 1;
  transition: color 0.15s, background 0.15s;
}
.palette-toggle:hover {
  color: #ccc;
  background: #1a1a1a;
}

.palette-content {
  width: calc(100% - 32px);
  height: 100%;
  overflow-y: auto;
  background: var(--color-surface-panel);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}
</style>
