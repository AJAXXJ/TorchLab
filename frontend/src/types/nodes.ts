/** 端口定义 — 与后端 PortDef 对应 */
export interface PortDef {
  id: string
  label: string
  dtype: string
  required: boolean
}

/** 参数定义 — 驱动前端动态表单 */
export interface ParamDef {
  type: 'int' | 'float' | 'bool' | 'string' | 'choice'
  default: unknown
  required?: boolean
  min?: number
  max?: number
  options?: string[]
  description?: string
}

/** 节点元数据 — GET /api/nodes 返回格式 */
export interface NodeMeta {
  display_name: string
  category: string
  description: string
  is_custom: boolean
  params_schema: Record<string, ParamDef>
  ports: {
    inputs: PortDef[]
    outputs: PortDef[]
  }
}

/** API 返回 */
export interface NodesResponse {
  nodes: Record<string, NodeMeta>
}

/** 图生成请求 */
export interface GenerateRequest {
  nodes: Array<{
    id: number
    type: string
    pos: [number, number]
    properties: Record<string, unknown>
  }>
  links: Array<[number, number, number, number, number, string]>
}

/** 图生成响应 */
export interface GenerateResponse {
  code?: string
  shapes?: Record<string, number[]>
  errors?: Array<{ node_id?: number; message: string }>
}
