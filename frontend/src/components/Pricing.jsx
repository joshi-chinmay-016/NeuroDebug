import { motion } from 'framer-motion'
import { Check, Zap, Shield, Users, Infinite, Clock, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '../lib/utils'

const plans = [
  {
    name: 'Guest',
    description: 'Try NeuroDebug without an account',
    price: 'Free',
    features: [
      '3 requests per day',
      'Basic AST analysis',
      'Rule engine detection',
      'No account required',
      'No history saved',
      'No project management',
    ],
    limitations: [
      'No LLM analysis',
      'No patch generation',
      'No verification',
      'Temporary session only',
    ],
    cta: 'Start Free',
    ctaLink: '/debug',
    popular: false,
  },
  {
    name: 'Free',
    description: 'Perfect for individual developers',
    price: 'Free',
    features: [
      '5 requests per day',
      'All AST analysis features',
      'LLM-powered analysis',
      'Patch generation',
      'Execution verification',
      '3 projects',
      'Debug history',
      'Cross-device sync',
    ],
    limitations: [
      'Standard processing',
      'Basic reports',
      'No API access',
    ],
    cta: 'Get Started',
    ctaLink: '/debug',
    popular: false,
  },
  {
    name: 'Pro',
    description: 'For serious developers and teams',
    price: '$29',
    period: '/month',
    features: [
      '20+ requests per day',
      'Priority processing',
      'Unlimited projects',
      'Advanced reports',
      'API access',
      'Team collaboration',
      'Custom integrations',
      'Priority support',
      'Advanced analytics',
    ],
    limitations: [],
    cta: 'Start Pro Trial',
    ctaLink: '/debug',
    popular: true,
  },
  {
    name: 'Enterprise',
    description: 'For large organizations',
    price: 'Custom',
    features: [
      'Unlimited requests',
      'Dedicated infrastructure',
      'SSO/SAML integration',
      'Custom branding',
      'SLA guarantee',
      'Dedicated support',
      'On-premise deployment',
      'Custom training',
      'Audit logs',
    ],
    limitations: [],
    cta: 'Contact Sales',
    ctaLink: '/contact',
    popular: false,
  },
]

const featureIcons = {
  'Requests per day': Zap,
  'Projects': Users,
  'Processing': Clock,
  'Support': Shield,
  'API': Infinite,
}

export default function Pricing() {
  return (
    <div className="container py-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-16"
      >
        <h1 className="text-4xl font-bold tracking-tight mb-4">Simple, Transparent Pricing</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Choose the plan that's right for you. All plans include our core debugging features.
        </p>
      </motion.div>

      <div className="grid gap-8 lg:grid-cols-4">
        {plans.map((plan, index) => (
          <motion.div
            key={plan.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className={cn(
              "relative rounded-2xl border p-8 shadow-sm",
              plan.popular
                ? "border-primary bg-gradient-to-b from-primary/5 to-card"
                : "border-border/40 bg-card"
            )}
          >
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="inline-flex items-center rounded-full bg-primary px-3 py-1 text-xs font-medium text-primary-foreground">
                  Most Popular
                </span>
              </div>
            )}

            <div className="mb-6">
              <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
              <p className="text-sm text-muted-foreground mb-4">{plan.description}</p>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold">{plan.price}</span>
                {plan.period && (
                  <span className="text-muted-foreground">{plan.period}</span>
                )}
              </div>
            </div>

            <Link
              to={plan.ctaLink}
              className={cn(
                "w-full inline-flex items-center justify-center rounded-lg py-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                plan.popular
                  ? "bg-primary text-primary-foreground hover:bg-primary/90"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              )}
            >
              {plan.cta}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>

            <div className="mt-8 space-y-4">
              <div className="space-y-3">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-start gap-3">
                    <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
              </div>

              {plan.limitations.length > 0 && (
                <div className="pt-4 border-t border-border/40">
                  <p className="text-xs font-medium text-muted-foreground mb-3">
                    Limitations
                  </p>
                  <div className="space-y-2">
                    {plan.limitations.map((limitation) => (
                      <div key={limitation} className="flex items-start gap-3">
                        <div className="h-5 w-5 flex-shrink-0 mt-0.5 flex items-center justify-center">
                          <div className="h-1 w-1 rounded-full bg-muted-foreground" />
                        </div>
                        <span className="text-sm text-muted-foreground">{limitation}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* FAQ Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="mt-20"
      >
        <h2 className="text-2xl font-bold text-center mb-8">Frequently Asked Questions</h2>
        <div className="grid gap-6 md:grid-cols-2 max-w-4xl mx-auto">
          <div className="rounded-xl border border-border/40 bg-card p-6">
            <h3 className="font-semibold mb-2">Can I switch plans?</h3>
            <p className="text-sm text-muted-foreground">
              Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately.
            </p>
          </div>
          <div className="rounded-xl border border-border/40 bg-card p-6">
            <h3 className="font-semibold mb-2">What happens if I exceed my limit?</h3>
            <p className="text-sm text-muted-foreground">
              You'll receive a notification and can either upgrade your plan or wait for your daily limit to reset.
            </p>
          </div>
          <div className="rounded-xl border border-border/40 bg-card p-6">
            <h3 className="font-semibold mb-2">Is there a free trial?</h3>
            <p className="text-sm text-muted-foreground">
              The Guest and Free plans are always free. Pro plans include a 7-day trial for new users.
            </p>
          </div>
          <div className="rounded-xl border border-border/40 bg-card p-6">
            <h3 className="font-semibold mb-2">Do you offer refunds?</h3>
            <p className="text-sm text-muted-foreground">
              Yes, we offer a 30-day money-back guarantee for all paid plans.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
