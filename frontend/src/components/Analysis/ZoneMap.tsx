'use client'

import { useState } from 'react'
import { ZoneDetail } from './ZoneDetail'

interface Zone {
  zone_id: string
  row: number
  col: number
  health: number
  status: 'healthy' | 'moderate' | 'degraded' | 'critical'
  ndvi: number
  ndwi: number
  moisture: number
  alerts: string[]
  recommendations: string[]
  data_quality: number
}

interface ZonalAnalysis {
  farm_id: string
  grid_size: { rows: number; cols: number }
  overall_health: number
  zones: Zone[]
  problem_zones: string[]
  heatmap_data: number[][]
  summary: {
    status: string
    emoji: string
    message: string
    healthy_zones: number
    problem_zones: number
    total_zones: number
    farmer_summary: string
    priority_actions: Array<{ zone: string; action: string; health: number }>
  }
}

interface ZoneMapProps {
  analysis: ZonalAnalysis
  onZoneClick?: (zone: Zone) => void
  compact?: boolean
}

const getHealthColor = (health: number): string => {
  if (health >= 75) return 'bg-green-500'
  if (health >= 55) return 'bg-yellow-500'
  if (health >= 35) return 'bg-orange-500'
  return 'bg-red-500'
}

const getHealthEmoji = (health: number): string => {
  if (health >= 75) return '🟢'
  if (health >= 55) return '🟡'
  if (health >= 35) return '🟠'
  return '🔴'
}

const getHealthTextColor = (health: number): string => {
  if (health >= 75) return 'text-green-700'
  if (health >= 55) return 'text-yellow-700'
  if (health >= 35) return 'text-orange-700'
  return 'text-red-700'
}

const getHealthBgLight = (health: number): string => {
  if (health >= 75) return 'bg-green-100 hover:bg-green-200'
  if (health >= 55) return 'bg-yellow-100 hover:bg-yellow-200'
  if (health >= 35) return 'bg-orange-100 hover:bg-orange-200'
  return 'bg-red-100 hover:bg-red-200'
}

export function ZoneMap({ analysis, onZoneClick, compact = false }: ZoneMapProps) {
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null)
  const { grid_size, zones, heatmap_data, summary } = analysis

  const handleZoneClick = (zone: Zone) => {
    setSelectedZone(zone)
    onZoneClick?.(zone)
  }

  // Create grid from zones
  const grid: (Zone | null)[][] = Array(grid_size.rows)
    .fill(null)
    .map(() => Array(grid_size.cols).fill(null))

  zones.forEach((zone) => {
    if (zone.row < grid_size.rows && zone.col < grid_size.cols) {
      grid[zone.row][zone.col] = zone
    }
  })

  if (compact) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900">Farm Health Map</h3>
          <span className={`text-lg font-bold ${getHealthTextColor(analysis.overall_health)}`}>
            {Math.round(analysis.overall_health)}
          </span>
        </div>
        
        {/* Compact grid */}
        <div 
          className="grid gap-1 mx-auto"
          style={{ 
            gridTemplateColumns: `repeat(${grid_size.cols}, minmax(0, 1fr))`,
            maxWidth: '200px'
          }}
        >
          {grid.map((row, rowIdx) =>
            row.map((zone, colIdx) => (
              <button
                key={`${rowIdx}-${colIdx}`}
                onClick={() => zone && handleZoneClick(zone)}
                className={`
                  aspect-square rounded-sm transition-all duration-200
                  ${zone ? getHealthBgLight(zone.health) : 'bg-gray-100'}
                  ${zone ? 'cursor-pointer' : 'cursor-default'}
                  ${selectedZone?.zone_id === zone?.zone_id ? 'ring-2 ring-blue-500' : ''}
                `}
                title={zone ? `${zone.zone_id}: ${zone.health}%` : 'No data'}
              >
                <span className="sr-only">
                  {zone ? `Zone ${zone.zone_id}: ${zone.health}% health` : 'No data'}
                </span>
              </button>
            ))
          )}
        </div>

        {/* Problem zones indicator */}
        {summary.problem_zones > 0 && (
          <p className="text-xs text-orange-600 mt-2 text-center">
            ⚠️ {summary.problem_zones} area{summary.problem_zones > 1 ? 's' : ''} need attention
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 px-6 py-4 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Your Farm Health Map</h2>
            <p className="text-green-100 text-sm mt-1">{summary.farmer_summary}</p>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold">{Math.round(analysis.overall_health)}</div>
            <div className="text-green-100 text-sm">Overall Health</div>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Zone Grid */}
        <div className="mb-6">
          <div 
            className="grid gap-2 mx-auto max-w-md"
            style={{ gridTemplateColumns: `repeat(${grid_size.cols}, minmax(0, 1fr))` }}
          >
            {grid.map((row, rowIdx) =>
              row.map((zone, colIdx) => (
                <button
                  key={`${rowIdx}-${colIdx}`}
                  onClick={() => zone && handleZoneClick(zone)}
                  className={`
                    aspect-square rounded-lg p-2 transition-all duration-200
                    flex flex-col items-center justify-center
                    ${zone ? getHealthBgLight(zone.health) : 'bg-gray-100'}
                    ${zone ? 'cursor-pointer shadow-sm hover:shadow-md' : 'cursor-default'}
                    ${selectedZone?.zone_id === zone?.zone_id ? 'ring-2 ring-blue-500 ring-offset-2' : ''}
                  `}
                >
                  {zone ? (
                    <>
                      <span className="text-2xl mb-1">{getHealthEmoji(zone.health)}</span>
                      <span className={`text-lg font-bold ${getHealthTextColor(zone.health)}`}>
                        {Math.round(zone.health)}
                      </span>
                      <span className="text-xs text-gray-600">{zone.zone_id}</span>
                    </>
                  ) : (
                    <span className="text-gray-400 text-sm">No data</span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Legend */}
        <div className="flex justify-center gap-4 mb-6 text-sm">
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-green-500"></span>
            <span>Healthy (75+)</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-yellow-500"></span>
            <span>Moderate (55-74)</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-orange-500"></span>
            <span>Needs Attention (35-54)</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-red-500"></span>
            <span>Critical (&lt;35)</span>
          </div>
        </div>

        {/* Priority Actions */}
        {summary.priority_actions.length > 0 && (
          <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
            <h3 className="font-semibold text-amber-800 mb-3 flex items-center gap-2">
              <span>⚠️</span>
              <span>Priority Actions</span>
            </h3>
            <ul className="space-y-2">
              {summary.priority_actions.map((action, idx) => (
                <li 
                  key={idx}
                  className="flex items-start gap-3 text-sm"
                >
                  <span className={`font-medium ${getHealthTextColor(action.health)}`}>
                    {action.zone}:
                  </span>
                  <span className="text-gray-700">{action.action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Selected Zone Detail */}
        {selectedZone && (
          <div className="mt-6">
            <ZoneDetail 
              zone={selectedZone} 
              onClose={() => setSelectedZone(null)} 
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default ZoneMap

