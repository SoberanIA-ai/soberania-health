export function confBarColor(v?: number | null): string {
  if (v == null) return '#9ca3af'
  if (v >= 0.80) return '#16a34a'
  if (v >= 0.60) return '#d97706'
  return '#dc2626'
}

export function ConfidenceBar({ value, maxWidth = 120 }: { value?: number | null; maxWidth?: number }) {
  if (value == null) return <span className="text-gray-400 text-xs">–</span>
  const pct = Math.round(value * 100)
  const color = confBarColor(value)
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-1.5 rounded-full bg-gray-200 overflow-hidden" style={{ width: maxWidth }}>
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-xs font-semibold" style={{ color }}>{pct}%</span>
    </div>
  )
}
