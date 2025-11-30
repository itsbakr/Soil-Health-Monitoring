'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'

// Dynamically import map components to avoid SSR issues
const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { 
  ssr: false,
  loading: () => <div className="w-full h-full bg-gray-100 animate-pulse rounded-lg flex items-center justify-center">
    <span className="text-gray-500">Loading map...</span>
  </div>
})
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false })
const Rectangle = dynamic(() => import('react-leaflet').then(mod => mod.Rectangle), { ssr: false })
const Tooltip = dynamic(() => import('react-leaflet').then(mod => mod.Tooltip), { ssr: false })
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), { ssr: false })

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

interface ZoneMapOverlayProps {
  analysis: ZonalAnalysis
  latitude: number
  longitude: number
  area: number // in hectares
  onZoneClick?: (zone: Zone) => void
  className?: string
}

// Calculate zone bounds based on farm center and area
const calculateZoneBounds = (
  centerLat: number,
  centerLon: number,
  areaHectares: number,
  gridRows: number,
  gridCols: number,
  row: number,
  col: number
): [[number, number], [number, number]] => {
  // Convert hectares to approximate square side in meters
  // 1 hectare = 10,000 m²
  const totalAreaM2 = areaHectares * 10000
  const sideLengthM = Math.sqrt(totalAreaM2)
  
  // Convert meters to degrees (approximate)
  // 1 degree latitude ≈ 111,320 meters
  // 1 degree longitude ≈ 111,320 * cos(latitude) meters
  const latDegPerMeter = 1 / 111320
  const lonDegPerMeter = 1 / (111320 * Math.cos(centerLat * Math.PI / 180))
  
  const halfSideLat = (sideLengthM / 2) * latDegPerMeter
  const halfSideLon = (sideLengthM / 2) * lonDegPerMeter
  
  // Farm bounds
  const farmNorth = centerLat + halfSideLat
  const farmSouth = centerLat - halfSideLat
  const farmWest = centerLon - halfSideLon
  const farmEast = centerLon + halfSideLon
  
  // Zone size
  const zoneHeight = (farmNorth - farmSouth) / gridRows
  const zoneWidth = (farmEast - farmWest) / gridCols
  
  // Zone bounds (row 0 is north, col 0 is west)
  const north = farmNorth - (row * zoneHeight)
  const south = north - zoneHeight
  const west = farmWest + (col * zoneWidth)
  const east = west + zoneWidth
  
  return [[south, west], [north, east]]
}

// Get zone color based on health score
const getZoneColor = (health: number): string => {
  if (health >= 75) return '#22c55e' // green-500
  if (health >= 55) return '#eab308' // yellow-500
  if (health >= 35) return '#f97316' // orange-500
  return '#ef4444' // red-500
}

const getZoneFillOpacity = (health: number): number => {
  // More critical = more visible
  if (health >= 75) return 0.3
  if (health >= 55) return 0.4
  if (health >= 35) return 0.5
  return 0.6
}

const getHealthEmoji = (health: number): string => {
  if (health >= 75) return '🟢'
  if (health >= 55) return '🟡'
  if (health >= 35) return '🟠'
  return '🔴'
}

export function ZoneMapOverlay({ 
  analysis, 
  latitude, 
  longitude, 
  area,
  onZoneClick,
  className = "h-96 w-full"
}: ZoneMapOverlayProps) {
  const [isClient, setIsClient] = useState(false)
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null)
  
  const { grid_size, zones } = analysis

  useEffect(() => {
    setIsClient(true)
  }, [])

  const handleZoneClick = (zone: Zone) => {
    setSelectedZone(zone)
    onZoneClick?.(zone)
  }

  if (!isClient) {
    return (
      <div className={`${className} bg-gray-100 animate-pulse flex items-center justify-center rounded-xl`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-2"></div>
          <span className="text-gray-500 text-sm">Loading zone map...</span>
        </div>
      </div>
    )
  }

  // Calculate bounds for all zones
  const zoneBounds = zones.map(zone => ({
    zone,
    bounds: calculateZoneBounds(latitude, longitude, area, grid_size.rows, grid_size.cols, zone.row, zone.col)
  }))

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-4 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <span>🗺️</span> Farm Health Map Overlay
            </h2>
            <p className="text-emerald-100 text-sm mt-1">
              Click on any zone to see details • Satellite view shows actual farm location
            </p>
          </div>
          <div className="text-center bg-white/10 rounded-lg px-4 py-2">
            <div className="text-3xl font-bold">{Math.round(analysis.overall_health)}</div>
            <div className="text-emerald-100 text-xs">Overall Health</div>
          </div>
        </div>
      </div>

      {/* Map Container */}
      <div className={className}>
        <MapContainer
          center={[latitude, longitude]}
          zoom={16}
          style={{ height: '100%', width: '100%' }}
          className="z-0"
        >
          {/* Satellite/Aerial Imagery */}
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution='&copy; Esri'
          />
          
          {/* Overlay labels */}
          <TileLayer
            url="https://stamen-tiles.a.ssl.fastly.net/toner-labels/{z}/{x}/{y}.png"
            attribution='&copy; Stamen Design'
            opacity={0.7}
          />
          
          {/* Zone Rectangles */}
          {zoneBounds.map(({ zone, bounds }) => (
            <Rectangle
              key={zone.zone_id}
              bounds={bounds}
              pathOptions={{
                color: getZoneColor(zone.health),
                weight: selectedZone?.zone_id === zone.zone_id ? 4 : 2,
                fillColor: getZoneColor(zone.health),
                fillOpacity: getZoneFillOpacity(zone.health),
                dashArray: selectedZone?.zone_id === zone.zone_id ? undefined : '5,5'
              }}
              eventHandlers={{
                click: () => handleZoneClick(zone)
              }}
            >
              <Tooltip permanent direction="center" className="zone-tooltip">
                <div className="text-center font-bold">
                  <span className="text-lg">{getHealthEmoji(zone.health)}</span>
                  <br />
                  <span className="text-sm">{Math.round(zone.health)}</span>
                </div>
              </Tooltip>
            </Rectangle>
          ))}
          
          {/* Center Marker */}
          <Marker position={[latitude, longitude]} />
        </MapContainer>
      </div>

      {/* Grid Info & Legend */}
      <div className="p-4 bg-gray-50 border-t border-gray-200">
        {/* Grid Size Info */}
        <div className="flex items-center justify-center gap-6 mb-4 text-sm">
          <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg shadow-sm">
            <span className="text-gray-500">📐 Grid:</span>
            <span className="font-bold text-gray-800">{grid_size.rows}×{grid_size.cols}</span>
            <span className="text-gray-500">({grid_size.rows * grid_size.cols} zones)</span>
          </div>
          <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg shadow-sm">
            <span className="text-gray-500">📏 Farm:</span>
            <span className="font-bold text-gray-800">{area.toFixed(1)} ha</span>
          </div>
          <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg shadow-sm">
            <span className="text-gray-500">⚠️ Problem Zones:</span>
            <span className={`font-bold ${analysis.problem_zones.length > 0 ? 'text-red-600' : 'text-green-600'}`}>
              {analysis.problem_zones.length}
            </span>
          </div>
        </div>
        
        {/* Color Legend */}
        <div className="flex flex-wrap justify-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-green-500"></span>
            <span>Healthy (75+)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-yellow-500"></span>
            <span>Moderate (55-74)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-orange-500"></span>
            <span>Needs Attention (35-54)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 rounded bg-red-500"></span>
            <span>Critical (&lt;35)</span>
          </div>
        </div>
      </div>

      {/* Selected Zone Detail Panel */}
      {selectedZone && (
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                {getHealthEmoji(selectedZone.health)} Zone {selectedZone.zone_id}
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  selectedZone.health >= 75 ? 'bg-green-100 text-green-800' :
                  selectedZone.health >= 55 ? 'bg-yellow-100 text-yellow-800' :
                  selectedZone.health >= 35 ? 'bg-orange-100 text-orange-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {selectedZone.status}
                </span>
              </h3>
              
              <div className="mt-2 grid grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Health</span>
                  <div className="font-bold text-lg">{Math.round(selectedZone.health)}%</div>
                </div>
                <div>
                  <span className="text-gray-500">NDVI</span>
                  <div className="font-bold">{selectedZone.ndvi.toFixed(2)}</div>
                </div>
                <div>
                  <span className="text-gray-500">Moisture</span>
                  <div className="font-bold">{(selectedZone.moisture * 100).toFixed(0)}%</div>
                </div>
                <div>
                  <span className="text-gray-500">Data Quality</span>
                  <div className="font-bold">{(selectedZone.data_quality * 100).toFixed(0)}%</div>
                </div>
              </div>

              {selectedZone.alerts.length > 0 && (
                <div className="mt-3">
                  <h4 className="text-sm font-medium text-red-700">⚠️ Alerts:</h4>
                  <ul className="text-sm text-red-600 list-disc list-inside">
                    {selectedZone.alerts.map((alert, idx) => (
                      <li key={idx}>{alert}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedZone.recommendations.length > 0 && (
                <div className="mt-3">
                  <h4 className="text-sm font-medium text-green-700">💡 Recommendations:</h4>
                  <ul className="text-sm text-green-600 list-disc list-inside">
                    {selectedZone.recommendations.slice(0, 2).map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            
            <button 
              onClick={() => setSelectedZone(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ZoneMapOverlay

