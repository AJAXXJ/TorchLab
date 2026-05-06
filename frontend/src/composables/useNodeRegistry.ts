import { ref, type Ref } from 'vue'
import type { NodeMeta, GenerateRequest } from '@/types/nodes'
import { registerAllNodes } from '@/utils/litegraph-factory'

/** 统一响应包装 */
interface ApiResponse<T> {
  msg: string
  code: number
  data: T | null
}

interface NodesData { nodes: Record<string, NodeMeta> }
interface GenerateData { code: string; shapes: Record<string, number[]> }

/** 节点注册表 */
export function useNodeRegistry() {
  const metas: Ref<Record<string, NodeMeta>> = ref({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchNodes() {
    loading.value = true
    error.value = null
    try {
      const resp = await fetch('/api/nodes')
      if (!resp.ok) throw new Error(`${resp.status}`)
      const json: ApiResponse<NodesData> = await resp.json()
      if (json.code !== 0) throw new Error(json.msg)
      if (json.data) {
        metas.value = json.data.nodes
        registerAllNodes(json.data.nodes)
      }
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  function groupedMetas(): Record<string, Array<{ type: string; meta: NodeMeta }>> {
    const groups: Record<string, Array<{ type: string; meta: NodeMeta }>> = {}
    for (const [type, meta] of Object.entries(metas.value)) {
      const cat = meta.category || 'other'
      ;(groups[cat] ??= []).push({ type, meta })
    }
    return groups
  }

  return { metas, loading, error, fetchNodes, groupedMetas }
}

/** 代码生成 */
export function useCodeGenerate() {
  const code = ref('')
  const shapes = ref<Record<string, number[]>>({})
  const errors = ref<Array<{ node_id?: number; message: string }>>([])
  const generating = ref(false)

  async function generate(request: GenerateRequest) {
    generating.value = true
    code.value = ''
    shapes.value = {}
    errors.value = []
    try {
      const resp = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      })
      const json: ApiResponse<GenerateData> = await resp.json()
      if (json.code !== 0) {
        errors.value = [{ message: json.msg }]
      } else if (json.data) {
        code.value = json.data.code
        shapes.value = json.data.shapes
      }
    } catch (e) {
      errors.value = [{ message: (e as Error).message }]
    } finally {
      generating.value = false
    }
  }

  return { code, shapes, errors, generating, generate }
}
