export function iniciales(s?: string): string {
  return (s || '??').split(' ').slice(0, 2).map(w => w[0] || '').join('').toUpperCase() || '??'
}

export function capitalize(s?: string): string {
  return (s || '').charAt(0).toUpperCase() + (s || '').slice(1)
}

export function pct(n: number, total: number): number {
  return total > 0 ? Math.round((n / total) * 100) : 0
}

const AVATAR_COLORS = ['#3b82f6','#8b5cf6','#ec4899','#f59e0b','#10b981','#6366f1','#ef4444','#14b8a6']
export function avatarColor(name?: string): string {
  let h = 0
  for (const c of (name || '')) h = (h * 31 + c.charCodeAt(0)) & 0xffffffff
  return AVATAR_COLORS[Math.abs(h) % AVATAR_COLORS.length]
}

export function aseguraClass(s?: string): string {
  const m: Record<string, string> = { sanitas: 'text-red-700', adeslas: 'text-blue-700', dkv: 'text-green-700', mapfre: 'text-blue-900' }
  return m[(s || '').toLowerCase()] || 'text-gray-600'
}

export function fmtFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return Math.round(bytes / 1024) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

export function fmtDate(s?: string): string {
  if (!s) return '–'
  return new Date(s).toLocaleDateString('es-ES')
}

export function fmtDateTime(s?: string): string {
  if (!s) return '–'
  return new Date(s).toLocaleString('es-ES')
}
