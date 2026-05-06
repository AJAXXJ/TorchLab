/**
 * UE5 Blueprint-style node rendering callbacks for LiteGraph.
 *
 * Lifecycle: onDrawBackground (before default shape) → LiteGraph drawNodeShape
 * → onDrawForeground (after default shape + text).
 *
 * Strategy:
 * - onDrawBackground: drop shadow under the node (extends beyond default box edges)
 * - onDrawForeground: selection glow border + hover highlight (on top of everything)
 * - Header/body two-tone: achieved via node.color / node.bgcolor (set in factory),
 *   LiteGraph's default drawNodeShape already separates header from body.
 */

/** Slot/dtype → pin colors */
export const D_TYPE_SLOT_COLORS: Record<string, { on: string; off: string }> = {
  tensor: { on: '#4fc3f7', off: '#1a3a4a' },
  scalar: { on: '#81c784', off: '#1a3a2a' },
}

export const DEFAULT_SLOT_COLORS = { on: '#8ab4f8', off: '#2a3a4a' }

interface DrawContext {
  size: [number, number]
  color: string
  bgcolor: string
  type: string
  is_selected: boolean
  mouseOver?: boolean
}

function roundRectPath(
  ctx: CanvasRenderingContext2D,
  x: number, y: number,
  w: number, h: number, r: number,
): void {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.arcTo(x + w, y, x + w, y + r, r)
  ctx.lineTo(x + w, y + h - r)
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
  ctx.lineTo(x + r, y + h)
  ctx.arcTo(x, y + h, x, y + h - r, r)
  ctx.lineTo(x, y + r)
  ctx.arcTo(x, y, x + r, y, r)
  ctx.closePath()
}

/**
 * Draw drop shadow under the node.
 * Called BEFORE LiteGraph's default drawNodeShape, so the shadow extends
 * beyond the default box edges and remains visible underneath.
 */
export function drawUE5Background(this: DrawContext, ctx: CanvasRenderingContext2D): void {
  const node = this
  const w = node.size[0], h = node.size[1]

  ctx.save()
  ctx.shadowColor = 'rgba(0, 0, 0, 0.45)'
  ctx.shadowBlur = 12
  ctx.shadowOffsetX = 2
  ctx.shadowOffsetY = 2
  ctx.fillStyle = node.bgcolor || '#1a1a1a'
  roundRectPath(ctx, 0.5, 0.5, w, h, 8)
  ctx.fill()
  ctx.restore()
}

/**
 * Draw selection glow border + hover highlight.
 * Called AFTER LiteGraph's default drawNodeShape, so these sit on top.
 */
export function drawUE5Foreground(this: DrawContext, ctx: CanvasRenderingContext2D): void {
  const node = this
  const w = node.size[0], h = node.size[1]

  // Selection glow border (UE5-style gold)
  if (node.is_selected) {
    ctx.save()
    ctx.shadowColor = 'rgba(245, 158, 11, 0.35)'
    ctx.shadowBlur = 14
    ctx.shadowOffsetX = 0
    ctx.shadowOffsetY = 0
    ctx.strokeStyle = 'rgba(245, 158, 11, 0.55)'
    ctx.lineWidth = 2
    roundRectPath(ctx, 1.5, 1.5, w - 3, h - 3, 7)
    ctx.stroke()
    ctx.restore()
  }

  // Hover highlight
  if (node.mouseOver && !node.is_selected) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.04)'
    roundRectPath(ctx, 0.5, 0.5, w, h, 8)
    ctx.fill()
  }
}
