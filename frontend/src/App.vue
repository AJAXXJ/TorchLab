<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import NodePalette from '@/components/NodePalette.vue'
import LiteGraphCanvas from '@/components/LiteGraphCanvas.vue'
import InspectorPanel from '@/components/InspectorPanel.vue'
import { useNodeRegistry, useCodeGenerate } from '@/composables/useNodeRegistry'
import type { NodeMeta } from '@/types/nodes'

const { metas, loading, error, fetchNodes, groupedMetas } = useNodeRegistry()
const { code, errors, generating, generate } = useCodeGenerate()

const canvasRef = ref<InstanceType<typeof LiteGraphCanvas>>()
const selectedNode = ref<{
  id: number; nodeType: string; properties: Record<string, unknown>; meta: NodeMeta
} | null>(null)
const showCode = ref(false)

onMounted(() => fetchNodes())

function onAddNode(type: string) { canvasRef.value?.addNodeAtCenter(type) }
function onNodeSelected(node: typeof selectedNode.value) { selectedNode.value = node; showCode.value = false }
function onNodeDeselected() { selectedNode.value = null }
function onUpdateProperty(nodeId: number, key: string, value: unknown) {
  canvasRef.value?.updateNodeProperty(nodeId, key, value)
  if (selectedNode.value && selectedNode.value.id === nodeId) selectedNode.value.properties[key] = value
}
async function onGenerate() {
  if (!canvasRef.value) return
  await generate(canvasRef.value.getGraphData())
  showCode.value = true
}
function onClear() {
  canvasRef.value?.clearGraph()
  code.value = ''; errors.value = []; showCode.value = false; selectedNode.value = null
}
</script>

<template>
  <div class="h-screen flex flex-col bg-[var(--color-surface-deep)]">
    <AppHeader :generating="generating" @generate="onGenerate" @clear="onClear" />
    <div class="flex-1 relative overflow-hidden">
      <LiteGraphCanvas
        ref="canvasRef" :metas="metas" :active-node-id="selectedNode?.id ?? null"
        @node-selected="onNodeSelected" @node-deselected="onNodeDeselected"
      />
      <NodePalette
        :grouped="groupedMetas()" :loading="loading" :error="error"
        @add-node="onAddNode"
      />
      <InspectorPanel
        :selected-node="selectedNode" :generated-code="code"
        :generated-errors="errors" :show-code="showCode"
        @update-property="onUpdateProperty"
      />
    </div>
  </div>
</template>
