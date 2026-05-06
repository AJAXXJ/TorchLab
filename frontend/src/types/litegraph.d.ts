declare module 'litegraph.js' {
  interface WidgetOptions {
    min?: number
    max?: number
    step?: number
    values?: string[]
  }

  interface LGraphNode {
    id: number
    type: string
    pos: [number, number]
    size: [number, number]
    properties: Record<string, unknown>
    widgets_values?: Record<string, unknown>
    inputs: Array<{ name: string; type: string; link: number | null }>
    outputs: Array<{ name: string; type: string; links: number[] | null }>
    addInput(label: string, type: string, extra?: Record<string, unknown>): void
    addOutput(label: string, type: string, extra?: Record<string, unknown>): void
    addWidget(
      type: string,
      label: string,
      defaultValue: unknown,
      callbackOrProperty: string | ((v: unknown) => void),
      options?: WidgetOptions
    ): void
    getInputNode(slot: number): LGraphNode | null
    getOutputNode(slot: number): LGraphNode | null
  }

  interface SerializedGraph {
    nodes: Array<{
      id: number
      type: string
      pos: [number, number]
      size: [number, number]
      properties: Record<string, unknown>
      widgets_values?: Record<string, unknown>
    }>
    links: Array<[number, number, number, number, number, string]>
    groups: unknown[]
    config: Record<string, unknown>
  }

  class LGraph {
    add(node: LGraphNode): void
    remove(node: LGraphNode): void
    clear(): void
    start(): void
    stop(): void
    serialize(): SerializedGraph
    configure(data: SerializedGraph): void
    computeExecutionOrder(): number[]
    getNodeById(id: number): LGraphNode | null
    convertOffsetToCanvas(pos: [number, number]): [number, number]
  }

  class LGraphCanvas {
    constructor(element: HTMLElement | null, graph: LGraph)
    resize(): void
    draw(force?: boolean): void
    background_image: string
    onNodeSelected?: (node: LGraphNode) => void
    onNodeDeselected?: (node: LGraphNode) => void
  }

  const LiteGraph: {
    registerNodeType(type: string, nodeClass: new () => LGraphNode): void
    createNode(type: string): LGraphNode | null
    isValidConnection(a: LGraphNode, b: LGraphNode): boolean
  }

  export { LGraph, LGraphCanvas, LiteGraph }
  export type { LGraphNode, SerializedGraph }
}
