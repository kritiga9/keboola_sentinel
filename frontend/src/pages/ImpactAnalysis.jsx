import { useState, useEffect } from 'react'
import { ChevronDown, AlertTriangle } from 'lucide-react'
import KpiCard from '../components/KpiCard.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { fetchImpactTables, fetchImpactAnalysis } from '../api/client.js'

// ── Dependency graph rendered as SVG ─────────────────────────────────────────

const NODE_W = 170
const NODE_H = 52
const COL_GAP = 100
const ROW_GAP = 18
const PAD = 24

function truncate(str, n) {
  return str.length > n ? str.slice(0, n) + '…' : str
}

function nodeColor(type, side) {
  if (side === 'center') return { fill: '#3b82f6', text: '#fff', border: '#1d4ed8' }
  if (side === 'writer')  return { fill: '#16a34a', text: '#fff', border: '#15803d' }
  const t = (type || '').toLowerCase()
  if (t.includes('transformation')) return { fill: '#ca8a04', text: '#fff', border: '#a16207' }
  if (t.includes('writer'))         return { fill: '#dc2626', text: '#fff', border: '#b91c1c' }
  return { fill: '#64748b', text: '#fff', border: '#475569' }
}

function DependencyGraph({ writers, readers, tableName }) {
  const leftCount  = writers.length
  const rightCount = readers.length
  const maxRows    = Math.max(leftCount, rightCount, 1)

  const totalH = PAD * 2 + maxRows * NODE_H + (maxRows - 1) * ROW_GAP
  const totalW = PAD * 2 + NODE_W * 3 + COL_GAP * 2

  const centerX = PAD + NODE_W + COL_GAP
  const centerY = totalH / 2 - NODE_H / 2

  function rowY(count, i) {
    const blockH = count * NODE_H + (count - 1) * ROW_GAP
    const startY = (totalH - blockH) / 2
    return startY + i * (NODE_H + ROW_GAP)
  }

  const writerNodes = writers.map((w, i) => ({
    x: PAD,
    y: rowY(Math.max(leftCount, 1), i),
    label: truncate(w.config_name, 22),
    sub:   truncate(w.component_name, 20),
    color: nodeColor(w.component_type, 'writer'),
  }))

  const readerNodes = readers.map((r, i) => ({
    x: PAD + NODE_W * 2 + COL_GAP * 2,
    y: rowY(Math.max(rightCount, 1), i),
    label: truncate(r.config_name, 22),
    sub:   truncate(r.component_name, 20),
    color: nodeColor(r.component_type, 'reader'),
  }))

  const centerColor = nodeColor(null, 'center')

  return (
    <div className="overflow-x-auto">
      <svg width={totalW} height={Math.max(totalH, 120)} className="font-sans">
        {/* Writer → Center edges */}
        {writerNodes.map((w, i) => {
          const x1 = w.x + NODE_W
          const y1 = w.y + NODE_H / 2
          const x2 = centerX
          const y2 = centerY + NODE_H / 2
          const mx = (x1 + x2) / 2
          return (
            <path
              key={`we-${i}`}
              d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`}
              fill="none"
              stroke="#16a34a"
              strokeWidth="1.5"
              strokeOpacity="0.6"
              markerEnd="url(#arrowGreen)"
            />
          )
        })}

        {/* Center → Reader edges */}
        {readerNodes.map((r, i) => {
          const x1 = centerX + NODE_W
          const y1 = centerY + NODE_H / 2
          const x2 = r.x
          const y2 = r.y + NODE_H / 2
          const mx = (x1 + x2) / 2
          return (
            <path
              key={`re-${i}`}
              d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`}
              fill="none"
              stroke="#dc2626"
              strokeWidth="1.5"
              strokeOpacity="0.6"
              markerEnd="url(#arrowRed)"
            />
          )
        })}

        {/* Arrow markers */}
        <defs>
          <marker id="arrowGreen" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#16a34a" fillOpacity="0.7" />
          </marker>
          <marker id="arrowRed" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#dc2626" fillOpacity="0.7" />
          </marker>
        </defs>

        {/* Writer nodes */}
        {writerNodes.map((n, i) => (
          <g key={`wn-${i}`}>
            <rect x={n.x} y={n.y} width={NODE_W} height={NODE_H}
              rx="8" fill={n.color.fill} stroke={n.color.border} strokeWidth="1" />
            <text x={n.x + 10} y={n.y + 18} fill={n.color.text} fontSize="11" fontWeight="600">
              {n.label}
            </text>
            <text x={n.x + 10} y={n.y + 33} fill={n.color.text} fontSize="9.5" opacity="0.8">
              {n.sub}
            </text>
          </g>
        ))}

        {/* Center node */}
        <g>
          <rect
            x={centerX} y={centerY} width={NODE_W} height={NODE_H}
            rx="8"
            fill={centerColor.fill}
            stroke={centerColor.border}
            strokeWidth="2"
          />
          <text x={centerX + NODE_W / 2} y={centerY + 22} fill="white" fontSize="11" fontWeight="700" textAnchor="middle">
            {truncate(tableName, 22)}
          </text>
          <text x={centerX + NODE_W / 2} y={centerY + 36} fill="white" fontSize="9" opacity="0.8" textAnchor="middle">
            selected table
          </text>
        </g>

        {/* Reader nodes */}
        {readerNodes.map((n, i) => (
          <g key={`rn-${i}`}>
            <rect x={n.x} y={n.y} width={NODE_W} height={NODE_H}
              rx="8" fill={n.color.fill} stroke={n.color.border} strokeWidth="1" />
            <text x={n.x + 10} y={n.y + 18} fill={n.color.text} fontSize="11" fontWeight="600">
              {n.label}
            </text>
            <text x={n.x + 10} y={n.y + 33} fill={n.color.text} fontSize="9.5" opacity="0.8">
              {n.sub}
            </text>
          </g>
        ))}

        {/* Empty state */}
        {writers.length === 0 && readers.length === 0 && (
          <text x={totalW / 2} y={totalH / 2} fill="#94a3b8" fontSize="13" textAnchor="middle">
            No dependencies found for this table
          </text>
        )}

        {/* Legend */}
        {(writers.length > 0 || readers.length > 0) && (
          <g transform={`translate(${PAD}, ${totalH - 18})`}>
            <rect width="10" height="10" rx="2" fill="#16a34a" y="-8" />
            <text x="14" fontSize="9" fill="#64748b">Writes to table</text>
            <rect x="100" width="10" height="10" rx="2" fill="#dc2626" y="-8" />
            <text x="114" fontSize="9" fill="#64748b">Reads from table</text>
            <rect x="220" width="10" height="10" rx="2" fill="#ca8a04" y="-8" />
            <text x="234" fontSize="9" fill="#64748b">Transformation</text>
          </g>
        )}
      </svg>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ImpactAnalysis({ selectedOrg }) {
  const [tables, setTables] = useState([])
  const [tablesLoading, setTablesLoading] = useState(false)
  const [selectedTable, setSelectedTable] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [error, setError] = useState(null)

  // Load table list
  useEffect(() => {
    setTablesLoading(true)
    setSelectedTable('')
    setAnalysis(null)
    fetchImpactTables(selectedOrg)
      .then(t => { setTables(t); if (t.length > 0) setSelectedTable(t[0]) })
      .catch(e => setError(e.message))
      .finally(() => setTablesLoading(false))
  }, [selectedOrg])

  // Load analysis when table changes
  useEffect(() => {
    if (!selectedTable) return
    setAnalysisLoading(true)
    setError(null)
    fetchImpactAnalysis(selectedTable, selectedOrg)
      .then(setAnalysis)
      .catch(e => setError(e.message))
      .finally(() => setAnalysisLoading(false))
  }, [selectedTable, selectedOrg])

  const readers       = analysis?.readers ?? []
  const writers       = analysis?.writers ?? []
  const affected      = analysis?.affected_tables ?? []
  const totalDeps     = analysis?.total_dependencies ?? 0

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="page-title">Schema Impact Analysis</h1>
        <p className="caption mt-1">
          Analyze dependencies before schema changes
          {selectedOrg !== 'All Organizations' && (
            <span className="ml-1 font-medium text-slate-700">· {selectedOrg}</span>
          )}
        </p>
      </div>

      {tablesLoading && <LoadingSpinner message="Building lineage index…" />}

      {!tablesLoading && tables.length === 0 && (
        <div className="card p-12 text-center text-slate-400">
          <p className="text-base font-medium">No tables found</p>
          <p className="text-sm mt-1">Try selecting a different organization.</p>
        </div>
      )}

      {!tablesLoading && tables.length > 0 && (
        <>
          {/* Table selector */}
          <div className="card p-5 mb-6">
            <label className="block text-xs font-medium text-slate-500 mb-2">Select a table to analyze impact</label>
            <div className="relative max-w-lg">
              <select
                value={selectedTable}
                onChange={e => setSelectedTable(e.target.value)}
                className="select pr-8"
              >
                {tables.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm mb-6">
              Error: {error}
            </div>
          )}

          {analysisLoading && <LoadingSpinner message="Analyzing dependencies…" />}

          {!analysisLoading && analysis && (
            <>
              {/* KPIs */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <KpiCard label="Downstream Configs" value={readers.length}      color="red"    sub="Read from table" />
                <KpiCard label="Upstream Configs"   value={writers.length}      color="green"  sub="Write to table" />
                <KpiCard label="Affected Tables"    value={affected.length}      color="purple" sub="Downstream outputs" />
                <KpiCard label="Total Dependencies" value={totalDeps}           color="blue" />
              </div>

              <div className="divider" />

              {/* Graph */}
              <div className="card p-6 mb-6">
                <h2 className="section-title mb-1">Dependency Graph</h2>
                <p className="caption mb-6">
                  Green nodes write to the selected table · Red/amber nodes read from it
                </p>
                <DependencyGraph
                  writers={writers}
                  readers={readers}
                  tableName={selectedTable}
                />
              </div>

              {/* Warning banner */}
              {(readers.length > 0 || affected.length > 0) && (
                <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                  <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-semibold text-amber-800">
                      Modifying <code className="font-mono bg-amber-100 px-1 rounded">{selectedTable}</code> will
                      affect <strong>{readers.length} config{readers.length !== 1 ? 's' : ''}</strong> and{' '}
                      <strong>{affected.length} downstream table{affected.length !== 1 ? 's' : ''}</strong>.
                    </p>
                    {affected.length > 0 && (
                      <ul className="mt-2 space-y-0.5 text-amber-700">
                        {affected.slice(0, 6).map((t, i) => (
                          <li key={i} className="font-mono text-xs">· {t}</li>
                        ))}
                        {affected.length > 6 && (
                          <li className="text-xs">and {affected.length - 6} more…</li>
                        )}
                      </ul>
                    )}
                  </div>
                </div>
              )}

              {readers.length === 0 && writers.length === 0 && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-xl text-green-700 text-sm">
                  No dependencies found — this table can be safely modified.
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
