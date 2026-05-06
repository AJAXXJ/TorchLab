<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { LGraph, LGraphCanvas, LiteGraph } from 'litegraph.js'
import type { LGraphNode, SerializedGraph } from 'litegraph.js'
import { addNodeToGraph } from '@/utils/litegraph-factory'
import type { NodeMeta, GenerateRequest } from '@/types/nodes'

const emit = defineEmits<{
  (e: 'node-selected', node: { id: number; type: string; nodeType: string; properties: Record<string, unknown>; meta: NodeMeta }): void
  (e: 'node-deselected'): void
}>()

const props = defineProps<{
  metas: Record<string, NodeMeta>
  activeNodeId: number | null
}>()

const containerRef = ref<HTMLDivElement>()
const canvasRef = ref<HTMLCanvasElement>()
let graph: LGraph
let canvas: LGraphCanvas

// ── 自定义右键菜单 ──
// 节点引用用普通变量存储，避免 Vue 深度 reactive 包装破坏 LiteGraph 节点对象
let ctxNode: LGraphNode | null = null
const ctxMenuVisible = ref(false)
const ctxMenuPos = ref({ x: 0, y: 0 })

function showContextMenu(node: LGraphNode, event: MouseEvent) {
  ctxNode = node
  const menuW = 130; const menuH = 72
  let left = event.clientX
  let top = event.clientY
  if (left + menuW > window.innerWidth) left = window.innerWidth - menuW - 4
  if (top + menuH > window.innerHeight) top = window.innerHeight - menuH - 4
  ctxMenuPos.value = { x: left, y: top }
  ctxMenuVisible.value = true
}

function closeContextMenu() {
  ctxMenuVisible.value = false
  ctxNode = null
}

function onCtxDelete() {
  if (ctxNode) {
    const id = ctxNode.id
    const node = graph.getNodeById(id)
    if (node) {
      // 若删除的是当前选中节点，通知父组件关闭 Inspector
      if (id === props.activeNodeId) emit('node-deselected')
      graph.remove(node)
      canvas.draw(true)
    }
  }
  closeContextMenu()
}

function onCtxClone() {
  if (ctxNode) {
    const id = ctxNode.id
    const node = graph.getNodeById(id)
    if (node) {
      const cloned = node.clone()
      if (cloned) {
        cloned.pos[0] += 30
        cloned.pos[1] += 30
        graph.add(cloned)
        canvas.draw(true)
      }
    }
  }
  closeContextMenu()
}

// ── 右键检测 (pointerdown 阶段，先于 contextmenu 事件) ──
function onPointerDown(e: PointerEvent) {
  if (e.button !== 2) return
  if (!canvas || !canvasRef.value) return

  const rect = canvasRef.value.getBoundingClientRect()
  const canvasPos = canvas.convertOffsetToCanvas([e.clientX - rect.left, e.clientY - rect.top])
  const node = graph.getNodeOnPos(canvasPos[0], canvasPos[1])

  if (node) {
    e.preventDefault()
    e.stopPropagation()
    showContextMenu(node, e)
  }
}

onMounted(() => {
  graph = new LGraph()
  canvas = new LGraphCanvas(canvasRef.value!, graph)
  canvas.background_image = ''
  // @ts-expect-error — CSS 已处理背景
  canvas.clear_background = false

  // ── UE5 Blueprint-style canvas config ──
  canvas.render_connection_arrows = true
  canvas.render_curved_connections = true
  canvas.connections_width = 2.5
  // @ts-expect-error
  canvas.default_link_color = '#4fc3f7'
  // @ts-expect-error
  canvas.title_text_font = '600 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  // @ts-expect-error
  LiteGraph.NODE_TITLE_COLOR = '#e0e0e0'
  // @ts-expect-error
  LiteGraph.NODE_TEXT_SIZE = 12

  // Link type colors for dtype-based connection coloring
  // @ts-expect-error
  if (LiteGraph.LGraphCanvas.link_type_colors) {
    // @ts-expect-error
    Object.assign(LiteGraph.LGraphCanvas.link_type_colors, {
      tensor: '#4fc3f7',
      scalar: '#81c784',
    })
  }

  // 禁用双击空白搜索
  // @ts-expect-error
  canvas.showSearchBox = () => {}

  // 禁用 LiteGraph widget 内联编辑弹窗 — 参数编辑统一走右侧 InspectorPanel
  // @ts-expect-error
  canvas.prompt = () => {}

  // ── 彻底禁用 LiteGraph 内置右键菜单 ──
  // 替换 ContextMenu 构造函数为空壳，任何代码路径试图 new LiteGraph.ContextMenu
  // 都只会得到一个不可见的死 div，不会渲染任何菜单
  // @ts-expect-error
  LiteGraph.ContextMenu = class {
    root = document.createElement('div')
    constructor() { this.root.style.display = 'none' }
    // @ts-expect-error
    close() {}
    // @ts-expect-error
    getFirstEvent() { return { clientX: 0, clientY: 0 } }
    // @ts-expect-error
    getTopMenu() { return this }
    // @ts-expect-error
    addItem() {}
  }

  // 用 pointerdown 监听右键，走我们自己的浮动菜单
  canvasRef.value!.addEventListener('pointerdown', onPointerDown)

  canvas.onNodeSelected = (node: LGraphNode) => {
    const rawType = node.type
    const nodeType = rawType.split('/').pop() || rawType
    const meta = props.metas[nodeType]
    if (meta) {
      emit('node-selected', {
        id: node.id, type: rawType, nodeType,
        properties: { ...node.properties }, meta,
      })
    }
  }
  canvas.onNodeDeselected = () => { emit('node-deselected') }

  graph.start()
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  document.addEventListener('click', onDocumentClick)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCanvas)
  document.removeEventListener('click', onDocumentClick)
  if (canvasRef.value) {
    canvasRef.value.removeEventListener('pointerdown', onPointerDown)
  }
  graph.stop()
})

function onDocumentClick() {
  if (ctxMenuVisible.value) closeContextMenu()
}

function resizeCanvas() {
  if (!containerRef.value || !canvas) return
  canvas.resize(containerRef.value.clientWidth, containerRef.value.clientHeight)
}

function addNodeAtCenter(type: string) {
  const meta = props.metas[type]
  if (!meta || !canvas) return
  const cw = containerRef.value!.clientWidth
  const ch = containerRef.value!.clientHeight
  const pos = canvas.convertOffsetToCanvas([
    cw * 0.35 + Math.random() * 80, ch * 0.35 + Math.random() * 80
  ])
  addNodeToGraph(graph, type, meta, pos)
}

function addNodeAtPos(type: string, canvasX: number, canvasY: number) {
  const meta = props.metas[type]
  if (!meta) return
  addNodeToGraph(graph, type, meta, [canvasX, canvasY])
}

function getGraphData(): GenerateRequest {
  const data: SerializedGraph = graph.serialize()
  return {
    nodes: data.nodes.map(n => ({ id: n.id, type: n.type, pos: n.pos, properties: n.properties || {} })),
    links: data.links,
  }
}

function clearGraph() {
  graph.clear()
  emit('node-deselected')
}

function updateNodeProperty(nodeId: number, key: string, value: unknown) {
  const node = graph.getNodeById(nodeId)
  if (!node) return
  node.properties[key] = value
  if (node.widgets) {
    for (const w of node.widgets as Array<{ name?: string; value: unknown; options?: Record<string, unknown> }>) {
      if (w.name === key || w.options?.property === key) { w.value = value; break }
    }
  }
  canvas.draw(true)
}

function onDragOver(e: DragEvent) { e.preventDefault(); if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy' }

function onDrop(e: DragEvent) {
  e.preventDefault()
  const nodeType = e.dataTransfer?.getData('application/torchlab-node')
  if (!nodeType || !canvas) return
  const rect = canvasRef.value!.getBoundingClientRect()
  const pos = canvas.convertOffsetToCanvas([e.clientX - rect.left, e.clientY - rect.top])
  addNodeAtPos(nodeType, pos[0], pos[1])
}

defineExpose({ addNodeAtCenter, addNodeAtPos, getGraphData, clearGraph, updateNodeProperty })
</script>

<template>
  <div ref="containerRef" class="canvas-container" @dragover="onDragOver" @drop="onDrop">
    <canvas ref="canvasRef" />

    <Teleport to="body">
      <div
        v-if="ctxMenuVisible"
        class="ctx-menu"
        :style="{ left: ctxMenuPos.x + 'px', top: ctxMenuPos.y + 'px' }"
        @click.stop
      >
        <button class="ctx-item" @click="onCtxDelete">Delete</button>
        <button class="ctx-item" @click="onCtxClone">Clone</button>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.canvas-container {
  position: absolute;
  inset: 0;
  background-color: #0f0f0f;
  /* UE5-style grid: major lines every 96px, minor every 24px */
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px),
    linear-gradient(rgba(255, 255, 255, 0.018) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.018) 1px, transparent 1px);
  background-size:
    96px 96px,
    96px 96px,
    24px 24px,
    24px 24px;
}
canvas { display: block; width: 100%; height: 100%; }
</style>

<style>
.ctx-menu {
  position: fixed;
  z-index: 9999;
  min-width: 120px;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 4px 0;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
}
.ctx-item {
  display: block;
  width: 100%;
  padding: 5px 14px;
  text-align: left;
  font-size: 12px;
  color: #ccc;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.1s;
}
.ctx-item:hover {
  background: #2a2a2a;
  color: #fff;
}
</style>
