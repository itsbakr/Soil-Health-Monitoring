'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { HealthGauge } from '@/components/FarmerDashboard'

interface AdminStats {
  totalFarms: number
  totalArea: number
  averageHealth: number
  healthyFarms: number
  atRiskFarms: number
  criticalFarms: number
  recentAnalyses: number
  problemZonesDetected: number
}

interface FarmSummary {
  id: string
  name: string
  owner: string
  area: number
  health: number
  status: 'healthy' | 'moderate' | 'degraded' | 'critical'
  lastAnalysis: string
  problemZones: number
}

// Demo data for preview
const demoStats: AdminStats = {
  totalFarms: 247,
  totalArea: 3842,
  averageHealth: 68,
  healthyFarms: 142,
  atRiskFarms: 78,
  criticalFarms: 27,
  recentAnalyses: 156,
  problemZonesDetected: 89
}

const demoFarms: FarmSummary[] = [
  { id: '1', name: 'Valley Farm', owner: 'John M.', area: 45, health: 82, status: 'healthy', lastAnalysis: '2024-01-15', problemZones: 0 },
  { id: '2', name: 'Sunrise Fields', owner: 'Maria G.', area: 32, health: 65, status: 'moderate', lastAnalysis: '2024-01-14', problemZones: 2 },
  { id: '3', name: 'Green Acres', owner: 'David K.', area: 28, health: 45, status: 'degraded', lastAnalysis: '2024-01-14', problemZones: 5 },
  { id: '4', name: 'Oak Ridge', owner: 'Sarah L.', area: 52, health: 78, status: 'healthy', lastAnalysis: '2024-01-13', problemZones: 1 },
  { id: '5', name: 'River Bend', owner: 'James W.', area: 18, health: 32, status: 'critical', lastAnalysis: '2024-01-12', problemZones: 8 },
  { id: '6', name: 'Highland Farm', owner: 'Emma T.', area: 41, health: 71, status: 'moderate', lastAnalysis: '2024-01-12', problemZones: 2 },
]

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats>(demoStats)
  const [farms, setFarms] = useState<FarmSummary[]>(demoFarms)
  const [filter, setFilter] = useState<'all' | 'healthy' | 'at-risk' | 'critical'>('all')
  const router = useRouter()

  const filteredFarms = farms.filter(farm => {
    if (filter === 'all') return true
    if (filter === 'healthy') return farm.status === 'healthy'
    if (filter === 'at-risk') return farm.status === 'moderate' || farm.status === 'degraded'
    if (filter === 'critical') return farm.status === 'critical'
    return true
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-100 text-green-800'
      case 'moderate': return 'bg-yellow-100 text-yellow-800'
      case 'degraded': return 'bg-orange-100 text-orange-800'
      case 'critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-gradient-to-br from-emerald-600 to-green-700 rounded-xl flex items-center justify-center">
                <span className="text-xl">📊</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Partner Dashboard</h1>
                <p className="text-xs text-gray-500">SoilGuard Admin Portal</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">Demo Organization</span>
              <Link 
                href="/dashboard"
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Switch to Farmer View
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Demo Banner */}
      <div className="bg-gradient-to-r from-emerald-600 to-green-600 text-white py-3 px-4 text-center text-sm">
        <span className="mr-2">📢</span>
        <span>This is a preview of the Partner Dashboard. </span>
        <a href="mailto:partners@soilguard.app" className="underline font-medium">Contact us</a>
        <span> to get access for your organization.</span>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <span className="text-2xl">🏡</span>
              </div>
              <div>
                <p className="text-3xl font-bold text-gray-900">{stats.totalFarms}</p>
                <p className="text-sm text-gray-500">Total Farms</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <span className="text-2xl">📐</span>
              </div>
              <div>
                <p className="text-3xl font-bold text-gray-900">{stats.totalArea.toLocaleString()}</p>
                <p className="text-sm text-gray-500">Total Hectares</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-4">
              <HealthGauge score={stats.averageHealth} size="sm" showLabel={false} animated={false} />
              <div>
                <p className="text-3xl font-bold text-gray-900">{stats.averageHealth}</p>
                <p className="text-sm text-gray-500">Avg Health Score</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                <span className="text-2xl">⚠️</span>
              </div>
              <div>
                <p className="text-3xl font-bold text-gray-900">{stats.criticalFarms}</p>
                <p className="text-sm text-gray-500">Critical Farms</p>
              </div>
            </div>
          </div>
        </div>

        {/* Health Distribution */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Farm Health Distribution</h2>
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                <div className="flex h-full">
                  <div 
                    className="bg-green-500 h-full" 
                    style={{ width: `${(stats.healthyFarms / stats.totalFarms) * 100}%` }}
                  />
                  <div 
                    className="bg-yellow-500 h-full" 
                    style={{ width: `${(stats.atRiskFarms / stats.totalFarms) * 100}%` }}
                  />
                  <div 
                    className="bg-red-500 h-full" 
                    style={{ width: `${(stats.criticalFarms / stats.totalFarms) * 100}%` }}
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                <span className="text-gray-600">Healthy: {stats.healthyFarms} ({Math.round((stats.healthyFarms / stats.totalFarms) * 100)}%)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-yellow-500 rounded-full"></span>
                <span className="text-gray-600">At Risk: {stats.atRiskFarms} ({Math.round((stats.atRiskFarms / stats.totalFarms) * 100)}%)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                <span className="text-gray-600">Critical: {stats.criticalFarms} ({Math.round((stats.criticalFarms / stats.totalFarms) * 100)}%)</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xl">🛰️</span>
                  <div>
                    <p className="font-medium text-gray-900">{stats.recentAnalyses}</p>
                    <p className="text-xs text-gray-500">Analyses this week</p>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xl">🔍</span>
                  <div>
                    <p className="font-medium text-gray-900">{stats.problemZonesDetected}</p>
                    <p className="text-xs text-gray-500">Problem zones detected</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Farms Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Enrolled Farms</h2>
            <div className="flex gap-2">
              {(['all', 'healthy', 'at-risk', 'critical'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                    filter === f 
                      ? 'bg-gray-900 text-white' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {f === 'all' ? 'All' : f.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                </button>
              ))}
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Farm</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Owner</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Area (ha)</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Health</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issues</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Analysis</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredFarms.map((farm) => (
                  <tr key={farm.id} className="hover:bg-gray-50 cursor-pointer">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{farm.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600">{farm.owner}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600">{farm.area}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              farm.health >= 75 ? 'bg-green-500' : 
                              farm.health >= 55 ? 'bg-yellow-500' : 
                              farm.health >= 35 ? 'bg-orange-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${farm.health}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-700">{farm.health}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(farm.status)}`}>
                        {farm.status.charAt(0).toUpperCase() + farm.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {farm.problemZones > 0 ? (
                        <span className="text-red-600 font-medium">{farm.problemZones} zones</span>
                      ) : (
                        <span className="text-green-600">None</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500 text-sm">
                      {new Date(farm.lastAnalysis).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Export Section */}
        <div className="mt-8 bg-gradient-to-r from-emerald-50 to-green-50 rounded-2xl border border-emerald-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">Export Impact Report</h3>
              <p className="text-sm text-gray-600">Download a comprehensive report for stakeholders</p>
            </div>
            <button className="bg-emerald-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-emerald-700 transition-colors flex items-center gap-2">
              <span>📥</span>
              Export PDF
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

