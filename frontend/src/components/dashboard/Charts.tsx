'use client'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'
import { Autorizacion } from '@/lib/types'
import { estadoLabel, estadoColor } from '@/components/ui/Badge'

function buildDonutData(autorizaciones: Autorizacion[]) {
  const counts: Record<string, number> = {}
  autorizaciones.forEach(a => { counts[a.estado] = (counts[a.estado] || 0) + 1 })
  return Object.entries(counts).map(([estado, value]) => ({ name: estadoLabel(estado), value, color: estadoColor(estado) }))
}

function buildBarData(autorizaciones: Autorizacion[]) {
  const counts: Record<string, number> = {}
  const colors: Record<string, string> = { Sanitas: '#ef4444', Adeslas: '#3b82f6', DKV: '#22c55e', Otras: '#9ca3af' }
  autorizaciones.forEach(a => {
    const k = (a.aseguradora || '').toLowerCase()
    const label = k === 'sanitas' ? 'Sanitas' : k === 'adeslas' ? 'Adeslas' : k === 'dkv' ? 'DKV' : 'Otras'
    counts[label] = (counts[label] || 0) + 1
  })
  return Object.entries(counts).map(([name, value]) => ({ name, value, color: colors[name] || '#9ca3af' }))
}

export function DonutChart({ autorizaciones }: { autorizaciones: Autorizacion[] }) {
  const data = buildDonutData(autorizaciones)
  return (
    <div className="bg-white rounded-xl p-5 border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Estado de autorizaciones</h3>
      <div style={{ height: 180 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={2}>
              {data.map((d, i) => <Cell key={i} fill={d.color} />)}
            </Pie>
            <Tooltip formatter={(v, n) => [v, n]} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
        {data.map((d, i) => (
          <div key={i} className="flex items-center gap-1 text-xs">
            <div className="w-2.5 h-2.5 rounded-sm" style={{ background: d.color }} />
            <span className="text-gray-600">{d.name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function AseguradoraChart({ autorizaciones }: { autorizaciones: Autorizacion[] }) {
  const data = buildBarData(autorizaciones)
  return (
    <div className="bg-white rounded-xl p-5 border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Por aseguradora</h3>
      <div style={{ height: 180 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barSize={32}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {data.map((d, i) => <Cell key={i} fill={d.color} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
