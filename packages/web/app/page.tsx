import Link from 'next/link'

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 border-b max-w-7xl mx-auto">
        <div className="text-2xl font-bold text-green-600">ClearPath</div>
        <div className="flex gap-4">
          <Link href="/sign-in" className="px-4 py-2 text-gray-600 hover:text-gray-900">Sign In</Link>
          <Link href="/sign-up" className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">Get Started Free</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-green-50 text-green-700 px-3 py-1 rounded-full text-sm font-medium mb-6">
          🌱 The first dual-substance recovery platform
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
          Quit Vaping & Weed.<br />
          <span className="text-green-600">Together, Finally.</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
          AI predicts your cravings before they hit. CBT therapy guides your recovery.
          Real-time support is always one tap away.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/sign-up" className="px-8 py-4 bg-green-600 text-white text-lg rounded-xl hover:bg-green-700 font-semibold">
            Get Started Free
          </Link>
          <Link href="#how-it-works" className="px-8 py-4 border-2 border-gray-200 text-gray-700 text-lg rounded-xl hover:border-gray-300 font-semibold">
            See How It Works
          </Link>
        </div>
        <p className="mt-4 text-sm text-gray-500">No credit card required. Free forever plan available.</p>
      </section>

      {/* Problem */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">The Gap No One Is Filling</h2>
          <p className="text-center text-gray-600 max-w-2xl mx-auto mb-12">
            38% of users vape AND use cannabis. Every other app treats these as separate problems. We don't.
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { stat: '38%', label: 'of vapers also use cannabis', desc: 'Dual-users are the largest growing segment with zero dedicated support' },
              { stat: '8 in 10', label: 'quit attempts fail alone', desc: 'Without prediction, CBT, and 24/7 AI support, cravings win' },
              { stat: '$2,500+', label: 'spent per year on average', desc: 'Combined vaping and cannabis costs most users face' },
            ].map((item) => (
              <div key={item.stat} className="bg-white rounded-2xl p-8 text-center shadow-sm">
                <div className="text-4xl font-bold text-green-600 mb-2">{item.stat}</div>
                <div className="font-semibold text-gray-900 mb-2">{item.label}</div>
                <div className="text-gray-600 text-sm">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">Everything You Need to Succeed</h2>
          <p className="text-center text-gray-600 max-w-2xl mx-auto mb-12">
            Built with addiction science, not willpower myths.
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { emoji: '🔮', title: 'AI Craving Predictor', desc: 'Gets notified 15–30 minutes before your predicted craving based on your personal patterns.' },
              { emoji: '🧠', title: '6-Week CBT Program', desc: 'Clinically-validated cognitive behavioral therapy, one lesson per day, personalized to your substance.' },
              { emoji: '💬', title: '24/7 AI Coach', desc: 'Claude-powered recovery coach that never judges, always available, and knows your history.' },
              { emoji: '📊', title: 'Health Timeline', desc: 'Watch your body heal in real-time with scientifically-sourced recovery milestones.' },
              { emoji: '🏆', title: 'Gamified Milestones', desc: 'Badges, streaks, and money-saved counters that make recovery feel like winning.' },
              { emoji: '🤝', title: 'Anonymous Community', desc: 'Connect with others on the same journey without revealing your identity.' },
            ].map((f) => (
              <div key={f.title} className="bg-gray-50 rounded-2xl p-8">
                <div className="text-4xl mb-4">{f.emoji}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-gray-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="bg-green-50 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">How ClearPath Works</h2>
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: '1', title: 'Build Your Profile', desc: 'Tell us about your usage patterns, quit goal, and timeline in 5 minutes.' },
              { step: '2', title: 'AI Learns Your Patterns', desc: 'After a few days of logging, our AI predicts when cravings will hit.' },
              { step: '3', title: 'Get Ahead of Cravings', desc: 'Receive push notifications 30 minutes before predicted cravings.' },
              { step: '4', title: 'Build Your New Life', desc: 'Track progress, earn badges, complete CBT, and connect with the community.' },
            ].map((s) => (
              <div key={s.step} className="text-center">
                <div className="w-12 h-12 bg-green-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">{s.step}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{s.title}</h3>
                <p className="text-gray-600 text-sm">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Real People, Real Results</h2>
          <div className="grid md:grid-cols-2 gap-8">
            {[
              { quote: "I tried quitting vaping 4 times before ClearPath. The craving predictor is genuinely magic — I got a notification 25 minutes before I normally crave and it gave me time to prepare.", name: 'Marcus T.', role: '67 days clean', substance: '🚭 Nicotine' },
              { quote: "I was a daily weed smoker for 8 years. The CBT program helped me understand WHY I was using for the first time. 3 months clean and counting.", name: 'Sarah K.', role: '90 days clean', substance: '🌿 Cannabis' },
              { quote: "The dual-user support is what sold me. Every other app only addressed one thing. I vaped and smoked weed and finally had a coach who understood both.", name: 'Devon M.', role: '45 days clean', substance: '🚭🌿 Both' },
              { quote: "The AI coach at 2am when I was having a terrible craving saved me. It felt like talking to someone who actually cared and knew exactly what to say.", name: 'Alex R.', role: '23 days clean', substance: '🚭 Nicotine' },
            ].map((t) => (
              <div key={t.name} className="bg-gray-50 rounded-2xl p-8">
                <p className="text-gray-700 mb-6 italic">"{t.quote}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center text-lg">{t.substance.split(' ')[0]}</div>
                  <div>
                    <div className="font-semibold text-gray-900">{t.name}</div>
                    <div className="text-sm text-green-600">{t.role} · {t.substance}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">Simple, Transparent Pricing</h2>
          <p className="text-center text-gray-600 mb-12">Less than your weekly habit costs.</p>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              {
                name: 'Free',
                price: '$0',
                period: 'forever',
                features: ['Basic tracker', '7-day history', '3 AI messages/day', 'All badges', 'Community read-only'],
                cta: 'Get Started',
                featured: false,
              },
              {
                name: 'Premium',
                price: '$9.99',
                period: 'per month',
                features: ['Unlimited AI coach', 'Full 6-week CBT program', 'Craving predictor + push alerts', 'Unlimited history + export', 'Community posts', 'Weekly AI insights'],
                cta: 'Start Free Trial',
                featured: true,
              },
              {
                name: 'Enterprise',
                price: '$4',
                period: 'per user/month',
                features: ['Everything in Premium', 'Employer wellness dashboard', 'Usage analytics', 'HIPAA-ready', 'SSO integration', 'Dedicated support'],
                cta: 'Contact Sales',
                featured: false,
              },
            ].map((plan) => (
              <div key={plan.name} className={`rounded-2xl p-8 ${plan.featured ? 'bg-green-600 text-white ring-4 ring-green-600' : 'bg-white'}`}>
                <div className={`text-sm font-medium mb-2 ${plan.featured ? 'text-green-100' : 'text-green-600'}`}>{plan.name}</div>
                <div className="text-4xl font-bold mb-1">{plan.price}</div>
                <div className={`text-sm mb-6 ${plan.featured ? 'text-green-100' : 'text-gray-500'}`}>{plan.period}</div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm">
                      <span>✓</span> {f}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/sign-up"
                  className={`block text-center py-3 rounded-xl font-semibold ${plan.featured ? 'bg-white text-green-600 hover:bg-green-50' : 'bg-green-600 text-white hover:bg-green-700'}`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Footer */}
      <section className="py-20 text-center">
        <div className="max-w-3xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Start Your Recovery Today</h2>
          <p className="text-xl text-gray-600 mb-8">Join thousands of people taking back control. It's free to start.</p>
          <Link href="/sign-up" className="inline-block px-10 py-4 bg-green-600 text-white text-lg rounded-xl hover:bg-green-700 font-semibold">
            Get Started Free →
          </Link>
          <div className="mt-12 pt-8 border-t text-sm text-gray-400">
            © 2025 ClearPath. All rights reserved.
          </div>
        </div>
      </section>
    </main>
  )
}
