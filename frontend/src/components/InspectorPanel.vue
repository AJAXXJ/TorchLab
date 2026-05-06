<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { NodeMeta } from '@/types/nodes'

const props = defineProps<{
  selectedNode: {
    id: number; nodeType: string; properties: Record<string, unknown>; meta: NodeMeta
  } | null
  generatedCode: string
  generatedErrors: Array<{ node_id?: number; message: string }>
  showCode: boolean
}>()

const emit = defineEmits<{ (e: 'update-property', nodeId: number, key: string, value: unknown): void }>()

// ── 面板折叠 ──
const isOpen = ref(false)

// 节点选中或代码生成时自动展开
watch(() => props.selectedNode, (n) => { if (n) isOpen.value = true })
watch(() => props.showCode, (s) => { if (s) isOpen.value = true })

const editValues = ref<Record<string, unknown>>({})
watch(() => props.selectedNode, (n) => {
  if (!n) return
  const merged: Record<string, unknown> = {}
  for (const [key, def] of Object.entries(n.meta.params_schema)) {
    merged[key] = (key in (n.properties || {})) ? n.properties[key] : def.default
  }
  editValues.value = merged
}, { immediate: true })

function onParamChange(key: string, value: unknown) {
  if (!props.selectedNode) return
  editValues.value[key] = value
  emit('update-property', props.selectedNode.id, key, value)
}

function catColor(cat: string): string {
  const m: Record<string, string> = {
    data: '#1a7a6b', layer: '#2c5aa0', activation: '#a0522c',
    control_flow: '#6b4090', custom: '#5a4080',
  }
  return m[cat] || '#555'
}

const sortedParams = computed(() =>
  props.selectedNode ? Object.entries(props.selectedNode.meta.params_schema) : []
)
</script>

<template>
  <div class="inspector-overlay" :class="{ closed: !isOpen }">
    <!-- Toggle tab — 左侧边缘 -->
    <button
      class="inspector-toggle"
      :title="isOpen ? 'Collapse panel' : 'Expand panel'"
      @click="isOpen = !isOpen"
    >
      <svg
        class="w-3 h-3 transition-transform duration-200"
        :class="{ 'rotate-180': !isOpen }"
        viewBox="0 0 12 14" fill="currentColor"
      >
        <path d="M0 0l12 7-12 7V0z" />
      </svg>
    </button>

    <!-- Content -->
    <div class="inspector-content">
      <!-- ── 节点详情 ── -->
      <template v-if="selectedNode && !showCode">
        <!-- Header -->
        <div class="flex items-center gap-1.5 mb-1">
          <span class="w-2 h-2 rounded-full flex-shrink-0" :style="{ background: catColor(selectedNode.meta.category) }"></span>
          <h2 class="text-sm font-semibold text-[#e0e0e0]">{{ selectedNode.meta.display_name }}</h2>
        </div>
        <div class="flex gap-1 mb-1.5">
          <span class="text-[9px] px-1.5 py-px bg-[#222] border border-[#333] rounded text-[#777]">
            {{ selectedNode.meta.category }}
          </span>
          <span
            v-if="selectedNode.meta.is_custom"
            class="text-[8px] px-1 py-px bg-[var(--color-accent)] text-black rounded font-bold"
          >custom</span>
        </div>
        <p class="text-[11px] text-[var(--color-text-dim)] mb-2.5">
          {{ selectedNode.meta.description }}
        </p>

        <!-- 参数 -->
        <div v-if="sortedParams.length" class="mb-3">
          <h3 class="text-[10px] uppercase text-[var(--color-text-subtle)] tracking-[0.5px] mb-1 pb-1 border-b border-[#222]">
            Parameters
          </h3>
          <div v-for="[key, def] in sortedParams" :key="key"
               :class="[
                 'mb-1',
                 (def.type === 'string' && (key === 'expression' || key === 'imports'))
                   ? 'flex-col' : 'flex items-center justify-between'
               ]">
            <label class="text-[11px] text-[#bbb] flex-shrink-0">{{ key }}</label>

            <!-- int -->
            <input
              v-if="def.type === 'int'"
              type="number" :value="editValues[key]" :min="def.min" :max="def.max" step="1"
              class="w-[110px] px-1.5 py-1 text-[11px] bg-[#222] border border-[#333]
                     rounded text-[#ccc] outline-none
                     focus:border-[var(--color-accent)]"
              @input="onParamChange(key, ($event.target as HTMLInputElement).valueAsNumber)"
            />
            <!-- float -->
            <input
              v-else-if="def.type === 'float'"
              type="number" :value="editValues[key]" :min="def.min" :max="def.max" step="0.01"
              class="w-[110px] px-1.5 py-1 text-[11px] bg-[#222] border border-[#333]
                     rounded text-[#ccc] outline-none
                     focus:border-[var(--color-accent)]"
              @input="onParamChange(key, parseFloat(($event.target as HTMLInputElement).value))"
            />
            <!-- bool -->
            <button
              v-else-if="def.type === 'bool'"
              class="relative inline-flex w-8 h-4.5 rounded-full transition-colors duration-200
                     border-none cursor-pointer p-0"
              :class="editValues[key] ? 'bg-[var(--color-accent)]' : 'bg-[#333]'"
              @click="onParamChange(key, !editValues[key])"
            >
              <span
                class="absolute top-0.5 w-3 h-3 rounded-full bg-[#111] transition-transform duration-200"
                :class="editValues[key] ? 'translate-x-4.5 left-0.5' : 'left-0.5'"
              ></span>
            </button>
            <!-- string -->
            <template v-else-if="def.type === 'string'">
              <div v-if="key === 'expression' || key === 'imports'" class="w-full mt-1">
                <textarea
                  :value="editValues[key]" rows="3"
                  class="w-full px-1.5 py-1 text-[11px] font-mono bg-[#111] border border-[#333]
                         rounded text-[#ccc] outline-none resize-y
                         focus:border-[var(--color-accent)]"
                  @input="onParamChange(key, ($event.target as HTMLTextAreaElement).value)"
                ></textarea>
              </div>
              <input
                v-else
                type="text" :value="editValues[key]"
                class="w-[110px] px-1.5 py-1 text-[11px] bg-[#222] border border-[#333]
                       rounded text-[#ccc] outline-none
                       focus:border-[var(--color-accent)]"
                @input="onParamChange(key, ($event.target as HTMLInputElement).value)"
              />
            </template>
            <!-- choice -->
            <select
              v-else-if="def.type === 'choice'"
              :value="editValues[key]"
              class="w-[110px] px-1.5 py-1 text-[11px] bg-[#222] border border-[#333]
                     rounded text-[#ccc] outline-none"
              @change="onParamChange(key, ($event.target as HTMLSelectElement).value)"
            >
              <option v-for="o in def.options" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
        </div>

        <!-- 端口 -->
        <div class="mb-3">
          <h3 class="text-[10px] uppercase text-[var(--color-text-subtle)] tracking-[0.5px] mb-1 pb-1 border-b border-[#222]">
            Ports
          </h3>
          <div class="text-[10px] text-[var(--color-text-subtle)] mb-0.5">Inputs</div>
          <div v-for="p in selectedNode.meta.ports.inputs" :key="p.id"
               class="flex items-center gap-1.5 py-px text-[11px] text-[#888]">
            <span class="text-[7px] text-[var(--color-accent)]">&#9654;</span>
            <span>{{ p.label }}</span>
            <span class="ml-auto text-[9px] text-[#444]">{{ p.dtype }}</span>
          </div>
          <div class="text-[10px] text-[var(--color-text-subtle)] mt-1.5 mb-0.5">Outputs</div>
          <div v-for="p in selectedNode.meta.ports.outputs" :key="p.id"
               class="flex items-center gap-1.5 py-px text-[11px] text-[#888]">
            <span class="text-[7px] text-[var(--color-accent)]">&#9654;</span>
            <span>{{ p.label }}</span>
            <span class="ml-auto text-[9px] text-[#444]">{{ p.dtype }}</span>
          </div>
        </div>
      </template>

      <!-- ── 代码视图 ── -->
      <template v-if="showCode">
        <h2 class="text-[13px] font-semibold text-[#e0e0e0] mb-2">Generated Code</h2>

        <div v-if="generatedErrors.length" class="flex flex-col gap-1 mb-2">
          <div
            v-for="(e, i) in generatedErrors" :key="i"
            class="px-2 py-1.5 bg-red-950 border border-red-900 rounded text-[11px] text-red-400"
          >
            <span v-if="e.node_id" class="font-semibold mr-1">#{{ e.node_id }}</span>
            {{ e.message }}
          </div>
        </div>

        <pre
          v-else
          class="flex-1 font-mono text-[11px] leading-relaxed whitespace-pre overflow-auto
                 bg-[var(--color-surface-card)] border border-[var(--color-border)]
                 rounded p-3 text-[#c9d1d9]"
        ><code>{{ generatedCode || 'Click "Generate Code" to produce a PyTorch module.' }}</code></pre>
      </template>

      <!-- ── 空状态 ── -->
      <div v-if="!selectedNode && !showCode" class="flex-1 flex items-center justify-center text-[11px] text-[#555]">
        Select a node to inspect
      </div>
    </div>
  </div>
</template>

<style scoped>
.inspector-overlay {
  position: absolute;
  right: 0; top: 0; bottom: 0;
  width: 290px;
  z-index: 20;
  transform: translateX(0);
  transition: transform 0.25s ease;
  display: flex;
}
.inspector-overlay.closed {
  transform: translateX(258px);
}

.inspector-toggle {
  position: absolute;
  left: 0; top: 50%;
  transform: translateY(-50%);
  width: 32px; height: 64px;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-surface-panel);
  border: 1px solid var(--color-border);
  border-right: none;
  border-radius: 6px 0 0 6px;
  color: #888;
  cursor: pointer;
  z-index: 1;
  transition: color 0.15s, background 0.15s;
}
.inspector-toggle:hover {
  color: #ccc;
  background: #1a1a1a;
}

.inspector-content {
  margin-left: 32px;
  flex: 1;
  height: 100%;
  overflow-y: auto;
  background: var(--color-surface-panel);
  border-left: 1px solid var(--color-border);
  padding: 14px;
  display: flex;
  flex-direction: column;
}
</style>
