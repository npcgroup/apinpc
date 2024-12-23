import { stringify } from 'csv-stringify/sync'

type ApiResponse = Record<string, any>

export function formatApiResponse(data: ApiResponse) {
  // Convert nested objects to flat structure
  const flattenObject = (obj: any, prefix = ''): Record<string, string> => {
    return Object.keys(obj).reduce((acc: Record<string, string>, k: string) => {
      const pre = prefix.length ? prefix + '.' : ''
      if (typeof obj[k] === 'object' && obj[k] !== null && !Array.isArray(obj[k])) {
        Object.assign(acc, flattenObject(obj[k], pre + k))
      } else {
        acc[pre + k] = Array.isArray(obj[k]) ? 
          `[${obj[k].length} items]` : 
          String(obj[k])
      }
      return acc
    }, {})
  }

  const flattened = flattenObject(data)
  
  // Convert to array format for table display
  return Object.entries(flattened).map(([key, value]) => ({
    key,
    value
  }))
}

export function convertToCSV(data: Array<{ key: string; value: string }>) {
  const rows = data.map(({ key, value }) => [key, value])
  return stringify([['Key', 'Value'], ...rows])
} 