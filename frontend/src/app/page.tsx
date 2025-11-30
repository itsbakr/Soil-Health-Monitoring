import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 via-white to-gray-50">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/20">
                <span className="text-xl">🌱</span>
              </div>
              <div>
                <span className="text-xl font-bold text-gray-900">SoilGuard</span>
                <span className="hidden sm:inline text-xs text-gray-500 ml-2">Farm Health Monitor</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Link 
                href="#partners" 
                className="hidden md:block text-gray-600 hover:text-gray-900 text-sm font-medium"
              >
                For Partners
              </Link>
              <Link 
                href="/auth/login" 
                className="text-gray-700 hover:text-gray-900 px-4 py-2 text-sm font-medium"
              >
                Sign In
              </Link>
              <Link 
                href="/auth/register" 
                className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:shadow-lg hover:scale-105 transition-all"
              >
                Get Started Free
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main>
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-green-100 text-green-800 px-4 py-2 rounded-full text-sm font-medium mb-8">
              <span>🛰️</span>
              <span>Powered by NASA Satellite Data & AI</span>
            </div>
            
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              Know Your Land.
              <br />
              <span className="bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                Grow Your Future.
              </span>
            </h1>
            
            <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
              Free satellite-powered soil health monitoring for farmers. Detect land degradation 
              early, get zone-by-zone recommendations, and protect your harvest.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Link 
                href="/auth/register" 
                className="bg-gradient-to-r from-green-500 to-emerald-600 text-white text-lg px-8 py-4 rounded-xl font-semibold shadow-lg shadow-green-500/25 hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center gap-2"
              >
                <span>🌾</span>
                Start Free Analysis
              </Link>
              <Link 
                href="#how-it-works" 
                className="bg-white text-gray-700 text-lg px-8 py-4 rounded-xl font-semibold border-2 border-gray-200 hover:border-green-500 hover:text-green-600 transition-all"
              >
                See How It Works
              </Link>
            </div>

            {/* Trust Badges */}
            <div className="flex flex-wrap justify-center gap-8 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>Free forever for farmers</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>Works offline</span>
              </div>
            </div>
          </div>
        </section>

        {/* Problem Section */}
        <section className="bg-red-50 py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto text-center">
              <span className="text-4xl mb-4 block">⚠️</span>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Land Degradation Threatens Livelihoods
              </h2>
              <p className="text-lg text-gray-700 mb-8">
                <strong>40% of the world's agricultural land is degraded.</strong> Farmers often don't 
                know until crop yields drop—by then, it's expensive to fix. Early detection can save 
                up to $500/hectare in remediation costs.
              </p>
              <div className="grid sm:grid-cols-3 gap-6">
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  <div className="text-3xl font-bold text-red-600 mb-2">2B+</div>
                  <div className="text-gray-600">Hectares degraded globally</div>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  <div className="text-3xl font-bold text-red-600 mb-2">$400B</div>
                  <div className="text-gray-600">Annual economic loss</div>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  <div className="text-3xl font-bold text-red-600 mb-2">12M</div>
                  <div className="text-gray-600">Hectares lost per year</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Get Farm Health in 3 Steps
              </h2>
              <p className="text-lg text-gray-600">
                Start in under 2 minutes. No equipment needed.
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">📍</span>
                </div>
                <div className="text-sm text-green-600 font-medium mb-2">Step 1</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Drop a Pin</h3>
                <p className="text-gray-600">
                  Mark your farm location on the map. No GPS device needed.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">🛰️</span>
                </div>
                <div className="text-sm text-blue-600 font-medium mb-2">Step 2</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">We Analyze</h3>
                <p className="text-gray-600">
                  Our AI analyzes NASA satellite data for your exact location.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-amber-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">🗺️</span>
                </div>
                <div className="text-sm text-amber-600 font-medium mb-2">Step 3</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">See Your Map</h3>
                <p className="text-gray-600">
                  Get a zone-by-zone health map showing exactly where to act.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="bg-gray-50 py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Built for Real Farmers
              </h2>
              <p className="text-lg text-gray-600">
                Simple tools that work in the field, not just the office.
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-4">
                  <span className="text-2xl">🗺️</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Zone Health Map</h3>
                <p className="text-gray-600">
                  See which areas of your farm need attention with our visual grid system.
                </p>
              </div>
              
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
                  <span className="text-2xl">📱</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Works Offline</h3>
                <p className="text-gray-600">
                  Access your farm data even without internet. Syncs when you're back online.
                </p>
              </div>
              
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center mb-4">
                  <span className="text-2xl">🌾</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Crop Recommendations</h3>
                <p className="text-gray-600">
                  Get AI-powered suggestions based on your soil, weather, and market prices.
                </p>
              </div>
              
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4">
                  <span className="text-2xl">⚡</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Early Alerts</h3>
                <p className="text-gray-600">
                  Detect degradation before it impacts your yield. Prevention is cheaper than cure.
                </p>
              </div>
              
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-pink-100 rounded-xl flex items-center justify-center mb-4">
                  <span className="text-2xl">💰</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">ROI Calculator</h3>
                <p className="text-gray-600">
                  Know your expected returns before you plant. Factor in costs and market prices.
                </p>
              </div>
              
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-teal-100 rounded-xl flex items-center justify-center mb-4">
                  <span className="text-2xl">📊</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Track Progress</h3>
                <p className="text-gray-600">
                  Monitor soil health over time. See how your land improves with each season.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* B2B Partner Section */}
        <section id="partners" className="py-20 bg-gradient-to-r from-emerald-900 to-green-900 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <div className="inline-flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full text-sm font-medium mb-6">
                  <span>🤝</span>
                  <span>For Organizations</span>
                </div>
                <h2 className="text-3xl md:text-4xl font-bold mb-6">
                  Partner With SoilGuard
                </h2>
                <p className="text-lg text-green-100 mb-8">
                  Help thousands of smallholder farmers protect their land. We provide the technology, 
                  you provide the reach.
                </p>
                
                <div className="space-y-4 mb-8">
                  <div className="flex items-start gap-3">
                    <span className="bg-white/20 rounded-lg p-1">✓</span>
                    <div>
                      <h4 className="font-semibold">NGOs & Development Programs</h4>
                      <p className="text-green-200 text-sm">Measure impact with real data on soil health improvements</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="bg-white/20 rounded-lg p-1">✓</span>
                    <div>
                      <h4 className="font-semibold">Government Agricultural Agencies</h4>
                      <p className="text-green-200 text-sm">Monitor regional soil health and target interventions</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="bg-white/20 rounded-lg p-1">✓</span>
                    <div>
                      <h4 className="font-semibold">Agricultural Cooperatives</h4>
                      <p className="text-green-200 text-sm">Aggregate insights across member farms</p>
                    </div>
                  </div>
                </div>
                
                <Link 
                  href="mailto:partners@soilguard.app"
                  className="inline-flex items-center gap-2 bg-white text-green-900 px-6 py-3 rounded-xl font-semibold hover:bg-green-50 transition-colors"
                >
                  <span>📧</span>
                  Contact for Partnership
                </Link>
              </div>
              
              <div className="bg-white/10 rounded-2xl p-8 backdrop-blur-sm">
                <h3 className="text-xl font-semibold mb-6">Partner Benefits</h3>
                <div className="space-y-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
                      <span className="text-2xl">📊</span>
                    </div>
                    <div>
                      <h4 className="font-medium">Admin Dashboard</h4>
                      <p className="text-green-200 text-sm">Aggregate view of all enrolled farms</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
                      <span className="text-2xl">📈</span>
                    </div>
                    <div>
                      <h4 className="font-medium">Impact Reports</h4>
                      <p className="text-green-200 text-sm">Measure soil health improvements over time</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
                      <span className="text-2xl">🔌</span>
                    </div>
                    <div>
                      <h4 className="font-medium">API Access</h4>
                      <p className="text-green-200 text-sm">Integrate with your existing systems</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
                      <span className="text-2xl">🎨</span>
                    </div>
                    <div>
                      <h4 className="font-medium">White-Label Option</h4>
                      <p className="text-green-200 text-sm">Brand with your organization's identity</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <span className="text-5xl mb-6 block">🌾</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Your Soil Is Talking. Are You Listening?
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              Join thousands of farmers already using satellite data to protect their land 
              and improve their yields.
            </p>
            <Link 
              href="/auth/register" 
              className="inline-flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white text-lg px-10 py-4 rounded-xl font-semibold shadow-lg shadow-green-500/25 hover:shadow-xl hover:scale-105 transition-all"
            >
              Start Free Analysis
              <span>→</span>
            </Link>
            <p className="text-sm text-gray-500 mt-4">
              Free forever for individual farmers. No credit card required.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-10 w-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
                  <span className="text-xl">🌱</span>
                </div>
                <span className="text-xl font-bold">SoilGuard</span>
              </div>
              <p className="text-gray-400 max-w-md">
                Empowering farmers with free satellite-powered soil health monitoring 
                to combat land degradation and improve food security.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="#how-it-works" className="hover:text-white transition-colors">How It Works</Link></li>
                <li><Link href="#partners" className="hover:text-white transition-colors">For Partners</Link></li>
                <li><Link href="/auth/register" className="hover:text-white transition-colors">Get Started</Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Contact</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="mailto:hello@soilguard.app" className="hover:text-white transition-colors">hello@soilguard.app</a></li>
                <li><a href="mailto:partners@soilguard.app" className="hover:text-white transition-colors">partners@soilguard.app</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-500 text-sm">
            <p>© 2024 SoilGuard. Built to fight land degradation.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
