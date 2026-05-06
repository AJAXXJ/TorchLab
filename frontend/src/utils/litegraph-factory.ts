import { LiteGraph } from 'litegraph.js'
import type { LGraphNode } from 'litegraph.js'
import type { NodeMeta } from '@/types/nodes'
import {
  drawUE5Background, drawUE5Foreground,
  D_TYPE_SLOT_COLORS, DEFAULT_SLOT_COLORS,
} from './litegraph-theme'

/** 分类 → 节点颜色映射 (UE5 Blueprint style) */
const CATEGORY_COLORS: Record<string, { color: string; bgcolor: string }> = {
  data:         { color: '#1a7a6b', bgcolor: '#1a2a2a' },
  layer:        { color: '#2c5aa0', bgcolor: '#1a2230' },
  activation:   { color: '#a0522c', bgcolor: '#2a2018' },
  control_flow: { color: '#6b4090', bgcolor: '#221a2c' },
  custom:       { color: '#5a4080', bgcolor: '#201a2a' },
}

const DEFAULT_COLORS = { color: '#444', bgcolor: '#222' }

/**
 * 根据后端元数据动态创建 LiteGraph 节点类.
 * 零硬编码 — 新增后端节点类型前端自动可见.
 *
 * 也被 LiteGraphCanvas 用于动态注册 Group 创建的组合节点.
 */
export function createLiteGraphNodeClass(nodeType: string, meta: NodeMeta): new () => LGraphNode {
  const catColors = CATEGORY_COLORS[meta.category] || DEFAULT_COLORS

  function DynamicNode(this: LGraphNode & {
    color: string; bgcolor: string
    onDrawBackground?: (ctx: CanvasRenderingContext2D) => void
    onDrawForeground?: (ctx: CanvasRenderingContext2D) => void
  }) {
    this.color = catColors.color
    this.bgcolor = catColors.bgcolor

    // Ports with dtype-colored pins
    for (const p of meta.ports.inputs) {
      const sc = D_TYPE_SLOT_COLORS[p.dtype] || DEFAULT_SLOT_COLORS
      this.addInput(p.label, p.dtype || 'tensor', {
        // @ts-expect-error — LiteGraph accepts slot shape/color extra_info
        shape: LiteGraph.CIRCLE_SHAPE,
        color_on: sc.on,
        color_off: sc.off,
      })
    }
    for (const p of meta.ports.outputs) {
      const sc = D_TYPE_SLOT_COLORS[p.dtype] || DEFAULT_SLOT_COLORS
      this.addOutput(p.label, p.dtype || 'tensor', {
        // @ts-expect-error
        shape: LiteGraph.CIRCLE_SHAPE,
        color_on: sc.on,
        color_off: sc.off,
      })
    }

    // LiteGraph addWidget stores default in widget.value but does NOT
    // write to this.properties — so we must sync manually for code gen.
    ;(this as any).properties = {}

    for (const [key, def] of Object.entries(meta.params_schema)) {
      const rawLabel = def.description || key
      const label = rawLabel.length > 14 ? rawLabel.slice(0, 13) + '…' : rawLabel
      const dflt = def.default

      switch (def.type) {
        case 'int':
          this.addWidget('number', label, dflt, key, {
            min: def.min ?? 1, max: def.max ?? 999999, step: 1,
          })
          break
        case 'float':
          this.addWidget('number', label, dflt, key, {
            min: def.min ?? 0, max: def.max ?? 1, step: 0.01,
          })
          break
        case 'bool':
          this.addWidget('toggle', label, dflt, key)
          break
        case 'string':
          this.addWidget('text', label, dflt, key)
          break
        case 'choice':
          this.addWidget('combo', label, dflt, key, {
            values: def.options ?? [],
          })
          break
        default:
          this.addWidget('text', label, String(dflt), key)
      }
      ;(this as any).properties[key] = dflt
    }

    // Dynamic minimum width — more params need wider node to avoid label/value overlap
    const widgetCount = Object.keys(meta.params_schema).length
    const minW = widgetCount > 5 ? 250 : widgetCount > 3 ? 230 : 210
    this.size[0] = Math.max(this.size[0], minW)

    // UE5 Blueprint-style rendering callbacks
    this.onDrawBackground = drawUE5Background
    this.onDrawForeground = drawUE5Foreground
  }

  DynamicNode.prototype.constructor = DynamicNode
  ;(DynamicNode as unknown as Record<string, string>).title = meta.display_name
  ;(DynamicNode as unknown as Record<string, string>).desc = meta.description || ''
  return DynamicNode as unknown as new () => LGraphNode
}

/** 注册所有后端节点到 LiteGraph */
export function registerAllNodes(metas: Record<string, NodeMeta>): void {
  for (const [type, meta] of Object.entries(metas)) {
    const lgType = `${meta.category}/${type}`
    LiteGraph.registerNodeType(lgType, createLiteGraphNodeClass(type, meta))
  }
}

/** 向画布添加节点 */
export function addNodeToGraph(
  graph: { add: (node: LGraphNode) => void },
  type: string,
  meta: NodeMeta,
  pos?: [number, number]
): LGraphNode | null {
  const lgType = `${meta.category}/${type}`
  const node = LiteGraph.createNode(lgType)
  if (!node) return null
  if (pos) node.pos = pos
  graph.add(node)
  return node
}
