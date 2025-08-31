import Link from 'next/link'
import { Leaf, BarChart3, Satellite, Brain } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-crop-50 to-soil-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-2">
              <Leaf className="h-8 w-8 text-crop-600" />
              <span className="text-xl font-bold text-gray-900">SoilGuard</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/auth/login" className="btn-secondary">
                Sign In
              </Link>
              <Link href="/auth/register" className="btn-primary">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Optimize Your Farm's{' '}
            <span className="text-crop-600">Soil Health</span> & ROI
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Make data-driven decisions about crop selection using satellite analysis, 
            AI-powered soil health assessment, and economic modeling to maximize both 
            sustainability and profitability.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/register" className="btn-primary text-lg px-8 py-3">
              Start Free Analysis
            </Link>
            <Link href="#features" className="btn-secondary text-lg px-8 py-3">
              Learn More
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <section id="features" className="mt-20">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="card text-center">
              <Satellite className="h-12 w-12 text-crop-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Satellite Analysis</h3>
              <p className="text-gray-600">
                Real-time soil health monitoring using Landsat satellite data and 
                vegetation indices.
              </p>
            </div>

            <div className="card text-center">
              <Brain className="h-12 w-12 text-crop-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">AI-Powered Insights</h3>
              <p className="text-gray-600">
                Advanced AI agents analyze soil conditions and provide actionable 
                recommendations.
              </p>
            </div>

            <div className="card text-center">
              <BarChart3 className="h-12 w-12 text-crop-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">ROI Optimization</h3>
              <p className="text-gray-600">
                Economic modeling to maximize profitability while improving 
                soil sustainability.
              </p>
            </div>

            <div className="card text-center">
              <Leaf className="h-12 w-12 text-crop-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Crop Recommendations</h3>
              <p className="text-gray-600">
                Data-driven crop selection based on soil health, weather, and 
                market conditions.
              </p>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="mt-20 text-center">
          <div className="bg-crop-600 rounded-2xl p-12 text-white">
            <h2 className="text-3xl font-bold mb-4">
              Ready to Transform Your Farming?
            </h2>
            <p className="text-xl mb-8 opacity-90">
              Join farmers worldwide who are using data science to improve 
              their soil health and profitability.
            </p>
            <Link href="/auth/register" className="bg-white text-crop-600 hover:bg-gray-100 font-medium py-3 px-8 rounded-lg transition-colors duration-200">
              Start Your Free Analysis
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <Leaf className="h-6 w-6 text-crop-400" />
              <span className="text-lg font-semibold">SoilGuard</span>
            </div>
            <p className="text-gray-400">
              Empowering farmers with satellite technology and AI insights
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
} 