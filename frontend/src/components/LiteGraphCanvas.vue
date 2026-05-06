<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { LGraph, LGraphCanvas, LiteGraph } from 'litegraph.js'
import type { LGraphNode, SerializedGraph } from 'litegraph.js'
import { addNodeToGraph } from '@/utils/litegraph-factory'
import type { NodeMeta, GenerateRequest } from '@/types/nodes'

const emit = defineEmits<{
  (e: 'node-selected', node: { id: number; type: string; nodeType: string; properties: Record<string, unknown>; meta: NodeMeta }): void
  (e: 'node-deselected'): void
  (e: 'refresh-nodes'): void
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
  // Determine if this is a multi-selection context
  const selCount = Object.keys(canvas.selected_nodes || {}).length
  const isMulti = selCount > 1 && canvas.selected_nodes[node.id]
  const menuW = isMulti ? 150 : 130
  const menuH = isMulti ? 108 : 72
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

// ── 组合节点对话框 ──
const groupDialogVisible = ref(false)
const groupName = ref('')
function openGroupDialog() {
  groupName.value = ''
  groupDialogVisible.value = true
  ctxMenuVisible.value = false
}
function closeGroupDialog() { groupDialogVisible.value = false }

async function onConfirmGroup() {
  const name = groupName.value.trim()
  if (!name) return
  closeGroupDialog()

  const selectedNodes = Object.values(canvas.selected_nodes || {}) as LGraphNode[]
  if (selectedNodes.length < 2) return

  const selectedIds = new Set(selectedNodes.map(n => n.id))

  // Serialize selected nodes
  const subNodes = selectedNodes.map(n => ({
    id: n.id, type: n.type, pos: n.pos, properties: { ...n.properties },
  }))

  // Classify links: internal vs external
  const subLinks: Array<unknown>[] = []
  const externalInputs: Array<{ node_id: number; port_idx: number; label: string }> = []
  const externalOutputs: Array<{ node_id: number; port_idx: number; label: string }> = []
  const seenInput = new Set<string>()
  const seenOutput = new Set<string>()

  // Track external link info for reconnection after group
  const reconnectInputs: Array<{ fromNode: number; fromSlot: number; toCompositeSlot: number; linkType: string }> = []
  const reconnectOutputs: Array<{ toNode: number; toSlot: number; fromCompositeSlot: number; linkType: string }> = []

  for (const linkId in graph.links) {
    const link = graph.links[linkId]
    const srcIn = selectedIds.has(link.origin_id)
    const tgtIn = selectedIds.has(link.target_id)

    if (srcIn && tgtIn) {
      subLinks.push(link.serialize())
    } else if (srcIn && !tgtIn) {
      const key = `${link.origin_id}:${link.origin_slot}`
      if (!seenOutput.has(key)) {
        seenOutput.add(key)
        const node = graph.getNodeById(link.origin_id)
        const port = node?.outputs?.[link.origin_slot]
        const idx = externalOutputs.length
        externalOutputs.push({ node_id: link.origin_id, port_idx: link.origin_slot, label: (node?.type?.split('/').pop() || '') + '.' + (port?.name || `out_${link.origin_slot}`) })
        reconnectOutputs.push({ toNode: link.target_id, toSlot: link.target_slot, fromCompositeSlot: idx, linkType: link.type || 'tensor' })
      }
    } else if (!srcIn && tgtIn) {
      const key = `${link.target_id}:${link.target_slot}`
      if (!seenInput.has(key)) {
        seenInput.add(key)
        const node = graph.getNodeById(link.target_id)
        const port = node?.inputs?.[link.target_slot]
        const idx = externalInputs.length
        externalInputs.push({ node_id: link.target_id, port_idx: link.target_slot, label: (node?.type?.split('/').pop() || '') + '.' + (port?.name || `in_${link.target_slot}`) })
        reconnectInputs.push({ fromNode: link.origin_id, fromSlot: link.origin_slot, toCompositeSlot: idx, linkType: link.type || 'tensor' })
      }
    }
  }

  // Also capture unconnected internal ports
  for (const n of selectedNodes) {
    for (let i = 0; i < (n.inputs || []).length; i++) {
      if (n.inputs[i].link == null) {
        const key = `${n.id}:${i}`
        if (!seenInput.has(key)) {
          seenInput.add(key)
          externalInputs.push({ node_id: n.id, port_idx: i, label: (n.type.split('/').pop() || '') + '.' + (n.inputs[i].name || `in_${i}`) })
        }
      }
    }
    for (let i = 0; i < (n.outputs || []).length; i++) {
      if (!n.outputs[i].links || n.outputs[i].links.length === 0) {
        const key = `${n.id}:${i}`
        if (!seenOutput.has(key)) {
          seenOutput.add(key)
          externalOutputs.push({ node_id: n.id, port_idx: i, label: (n.type.split('/').pop() || '') + '.' + (n.outputs[i].name || `out_${i}`) })
        }
      }
    }
  }

  // Compute center position
  let cx = 0, cy = 0
  for (const n of selectedNodes) { cx += n.pos[0]; cy += n.pos[1] }
  cx /= selectedNodes.length; cy /= selectedNodes.length

  let compositeNode: LGraphNode | null = null

  try {
    // Call API to create composite type
    const resp = await fetch('/api/composite/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        subgraph_nodes: subNodes,
        subgraph_links: subLinks,
        external_inputs: externalInputs,
        external_outputs: externalOutputs,
      }),
    })
    if (!resp.ok) throw new Error(`${resp.status}`)
    const json = await resp.json()
    if (json.code !== 0) throw new Error(json.msg)

    // Register the new node type with LiteGraph locally
    const nodeData = json.data.node
    const meta: NodeMeta = {
      display_name: nodeData.display_name,
      category: nodeData.category,
      description: `Composite: ${nodeData.display_name}`,
      is_custom: true,
      params_schema: {},
      ports: {
        inputs: externalInputs.map((ex, i) => ({ id: `in_${i}`, label: ex.label, dtype: 'tensor' })),
        outputs: externalOutputs.map((ex, i) => ({ id: `out_${i}`, label: ex.label, dtype: 'tensor' })),
      },
    }
    const { createLiteGraphNodeClass } = await import('@/utils/litegraph-factory')
    const lgType = `${meta.category}/${name}`
    LiteGraph.registerNodeType(lgType, createLiteGraphNodeClass(name, meta))

    // Remove selected nodes (and track if we removed the active node)
    let removedActive = false
    for (const n of selectedNodes) {
      if (n.id === props.activeNodeId) removedActive = true
      graph.remove(n)
    }
    if (removedActive) emit('node-deselected')

    // Add composite node
    compositeNode = LiteGraph.createNode(lgType)
    if (!compositeNode) throw new Error('Failed to create composite node')
    compositeNode.pos = [cx - 105, cy - 15]
    graph.add(compositeNode)

    // Reconnect external inputs
    for (const ri of reconnectInputs) {
      const fromNode = graph.getNodeById(ri.fromNode)
      if (fromNode && compositeNode) {
        fromNode.connect(ri.fromSlot, compositeNode, ri.toCompositeSlot)
      }
    }
    // Reconnect external outputs
    for (const ro of reconnectOutputs) {
      const toNode = graph.getNodeById(ro.toNode)
      if (toNode && compositeNode) {
        compositeNode.connect(ro.fromCompositeSlot, toNode, ro.toSlot)
      }
    }

    canvas.draw(true)
    autoSave()
    emit('refresh-nodes')
  } catch (e) {
    // Rollback: remove composite if created, TODO: show error
    if (compositeNode) {
      try { graph.remove(compositeNode) } catch (_) {}
    }
    alert('Failed to group nodes: ' + (e as Error).message)
  }
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

// ── 右键处理: 节点=菜单, 空画布=框选 ──
let rightDragging = false
let rightDragStart: [number, number] | null = null
const selectionRect = ref<{ x: number; y: number; w: number; h: number } | null>(null)

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
  } else {
    // Right-click on empty canvas — start drag-select
    e.preventDefault()
    e.stopPropagation()
    rightDragging = true
    rightDragStart = [e.clientX, e.clientY]
    selectionRect.value = null
    if (canvasRef.value) canvasRef.value.setPointerCapture(e.pointerId)
  }
}

function onPointerMove(e: PointerEvent) {
  if (!rightDragging || !rightDragStart) return
  const dx = e.clientX - rightDragStart[0]
  const dy = e.clientY - rightDragStart[1]
  if (Math.abs(dx) < 3 && Math.abs(dy) < 3) return
  selectionRect.value = {
    x: Math.min(rightDragStart[0], e.clientX),
    y: Math.min(rightDragStart[1], e.clientY),
    w: Math.abs(dx),
    h: Math.abs(dy),
  }
}

function onPointerUp(e: PointerEvent) {
  if (e.button !== 2) return
  if (!rightDragging) return
  rightDragging = false
  rightDragStart = null

  if (selectionRect.value && canvasRef.value) {
    const r = selectionRect.value
    const crect = canvasRef.value.getBoundingClientRect()
    // Convert screen rect → canvas coords
    const p1 = canvas.convertOffsetToCanvas([r.x - crect.left, r.y - crect.top])
    const p2 = canvas.convertOffsetToCanvas([r.x + r.w - crect.left, r.y + r.h - crect.top])
    const x1 = Math.min(p1[0], p2[0]); const y1 = Math.min(p1[1], p2[1])
    const x2 = Math.max(p1[0], p2[0]); const y2 = Math.max(p1[1], p2[1])

    const toSelect: LGraphNode[] = []
    for (const n of graph._nodes) {
      if (n.pos[0] + n.size[0] >= x1 && n.pos[0] <= x2 &&
          n.pos[1] + n.size[1] >= y1 && n.pos[1] <= y2) {
        toSelect.push(n)
      }
    }
    if (toSelect.length > 0) {
      canvas.selectNodes(toSelect)
      canvas.draw(true)
    }
    selectionRect.value = null
  }
  if (selectionRect.value === null && rightDragStart === null) {
    // Just a click on empty canvas — deselect all
    canvas.deselectAllNodes()
  }
}

// ── localStorage 自动保存 ──
const LS_KEY = 'torchlab-graph'
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null
function autoSave() {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = setTimeout(() => {
    try { localStorage.setItem(LS_KEY, JSON.stringify(graph.serialize())) } catch (_) {}
  }, 500)
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

  // 右键处理: 节点=菜单, 空画布=框选
  canvasRef.value!.addEventListener('pointerdown', onPointerDown)
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)

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

  // ── auto-save hooks ──
  graph.onNodeAdded = () => autoSave()
  graph.onNodeRemoved = () => autoSave()
  graph.onConnectionChange = () => autoSave()

  // localStorage restore
  try {
    const saved = localStorage.getItem(LS_KEY)
    if (saved) {
      const data = JSON.parse(saved)
      if (data.nodes && data.nodes.length) {
        graph.configure(data)
        canvas.draw(true)
      }
    }
  } catch (_) {}

  graph.start()
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  document.addEventListener('click', onDocumentClick)
})

onUnmounted(() => {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  window.removeEventListener('resize', resizeCanvas)
  document.removeEventListener('click', onDocumentClick)
  if (canvasRef.value) {
    canvasRef.value.removeEventListener('pointerdown', onPointerDown)
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', onPointerUp)
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
  autoSave()
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

function saveGraph(): string {
  return JSON.stringify(graph.serialize(), null, 2)
}

function loadGraph(json: string): boolean {
  const data = JSON.parse(json)
  graph.configure(data)
  canvas.draw(true)
  autoSave()
  return true
}

function hasContent(): boolean {
  return graph._nodes.length > 0
}

defineExpose({ addNodeAtCenter, addNodeAtPos, getGraphData, clearGraph, updateNodeProperty, saveGraph, loadGraph, hasContent })
</script>

<template>
  <div ref="containerRef" class="canvas-container" @dragover="onDragOver" @drop="onDrop">
    <canvas ref="canvasRef" />
    <!-- 右键框选矩形 -->
    <div
      v-if="selectionRect"
      class="select-rect"
      :style="{
        left: selectionRect.x + 'px',
        top: selectionRect.y + 'px',
        width: selectionRect.w + 'px',
        height: selectionRect.h + 'px',
      }"
    ></div>

    <Teleport to="body">
      <div
        v-if="ctxMenuVisible"
        class="ctx-menu"
        :style="{ left: ctxMenuPos.x + 'px', top: ctxMenuPos.y + 'px' }"
        @click.stop
      >
        <button class="ctx-item" @click="onCtxDelete">Delete</button>
        <button class="ctx-item" @click="onCtxClone">Clone</button>
        <button
          v-if="ctxNode && Object.keys(canvas.selected_nodes || {}).length > 1 && canvas.selected_nodes[ctxNode.id]"
          class="ctx-item ctx-item-accent"
          @click="openGroupDialog"
        >Group into Node</button>
      </div>

      <!-- Group naming dialog -->
      <div
        v-if="groupDialogVisible"
        class="ctx-overlay"
        @click.self="closeGroupDialog"
      >
        <div class="group-dialog" @click.stop>
          <h3 class="text-[13px] font-semibold text-[#e0e0e0] mb-3">Group into Node</h3>
          <label class="text-[11px] text-[#888] block mb-1">Node name</label>
          <input
            ref="groupNameInput"
            v-model="groupName"
            type="text"
            class="w-full px-2 py-1.5 text-[13px] bg-[#111] border border-[#333] rounded text-[#ccc] outline-none mb-3
                   focus:border-[var(--color-accent)]"
            placeholder="e.g. ConvBlock"
            @keydown.enter="onConfirmGroup"
            @keydown.escape="closeGroupDialog"
          />
          <div class="flex gap-2 justify-end">
            <button class="ctx-item px-3 py-1" @click="closeGroupDialog">Cancel</button>
            <button
              class="px-3 py-1 text-[12px] font-semibold bg-[var(--color-accent)] text-black rounded
                     hover:opacity-90 disabled:opacity-30 transition-opacity"
              :disabled="!groupName.trim()"
              @click="onConfirmGroup"
            >Create</button>
          </div>
        </div>
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
.select-rect {
  position: fixed;
  border: 1px solid rgba(245, 158, 11, 0.6);
  background: rgba(245, 158, 11, 0.08);
  pointer-events: none;
  z-index: 30;
}
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
.ctx-item-accent {
  color: #f5a623;
  border-top: 1px solid #2a2a2a;
  margin-top: 2px;
  padding-top: 6px;
}
.ctx-item-accent:hover {
  color: #f7c06c;
  background: #2a2020;
}
.ctx-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}
.group-dialog {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 20px;
  min-width: 280px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.7);
}
</style>
