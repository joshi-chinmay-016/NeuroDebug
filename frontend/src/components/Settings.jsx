// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion'
import { User, Bell, Shield, Palette, Key, Globe, Save } from 'lucide-react'
import { useState } from 'react'
import { cn } from '../lib/utils'

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile')
  const [settings, setSettings] = useState({
    profile: {
      name: 'Developer',
      email: 'dev@example.com',
      bio: 'Building amazing software',
    },
    notifications: {
      email: true,
      push: false,
      weekly: true,
    },
    appearance: {
      theme: 'dark',
      fontSize: 'medium',
    },
    api: {
      key: 'gsk_••••••••••••••••',
    },
  })

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'api', label: 'API Keys', icon: Key },
  ]

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account settings and preferences
        </p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Sidebar */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="lg:col-span-1"
        >
          <div className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                  activeTab === tab.id
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent text-muted-foreground"
                )}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="lg:col-span-3"
        >
          {activeTab === 'profile' && (
            <div className="rounded-xl border border-border/40 bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-6">Profile Settings</h2>
              <div className="space-y-6">
                <div>
                  <label className="text-sm font-medium mb-2 block">Display Name</label>
                  <input
                    type="text"
                    value={settings.profile.name}
                    onChange={(e) => setSettings({
                      ...settings,
                      profile: { ...settings.profile, name: e.target.value }
                    })}
                    className="w-full px-4 py-2 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Email</label>
                  <input
                    type="email"
                    value={settings.profile.email}
                    onChange={(e) => setSettings({
                      ...settings,
                      profile: { ...settings.profile, email: e.target.value }
                    })}
                    className="w-full px-4 py-2 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Bio</label>
                  <textarea
                    value={settings.profile.bio}
                    onChange={(e) => setSettings({
                      ...settings,
                      profile: { ...settings.profile, bio: e.target.value }
                    })}
                    rows={4}
                    className="w-full px-4 py-2 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="rounded-xl border border-border/40 bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-6">Notification Preferences</h2>
              <div className="space-y-4">
                {[
                  { id: 'email', label: 'Email notifications', description: 'Receive updates via email' },
                  { id: 'push', label: 'Push notifications', description: 'Receive browser push notifications' },
                  { id: 'weekly', label: 'Weekly digest', description: 'Get a weekly summary of activity' },
                ].map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                    <div>
                      <p className="font-medium text-sm">{item.label}</p>
                      <p className="text-xs text-muted-foreground">{item.description}</p>
                    </div>
                    <button
                      onClick={() => setSettings({
                        ...settings,
                        notifications: {
                          ...settings.notifications,
                          [item.id]: !settings.notifications[item.id]
                        }
                      })}
                      className={cn(
                        "w-12 h-6 rounded-full transition-colors relative",
                        settings.notifications[item.id] ? "bg-primary" : "bg-muted"
                      )}
                    >
                      <div
                        className={cn(
                          "w-5 h-5 rounded-full bg-white shadow transition-transform",
                          settings.notifications[item.id] ? "translate-x-6" : "translate-x-1"
                        )}
                      />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="rounded-xl border border-border/40 bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-6">Appearance</h2>
              <div className="space-y-6">
                <div>
                  <label className="text-sm font-medium mb-3 block">Theme</label>
                  <div className="grid grid-cols-3 gap-4">
                    {['light', 'dark', 'system'].map((theme) => (
                      <button
                        key={theme}
                        onClick={() => setSettings({
                          ...settings,
                          appearance: { ...settings.appearance, theme }
                        })}
                        className={cn(
                          "p-4 rounded-lg border text-sm font-medium transition-colors",
                          settings.appearance.theme === theme
                            ? "border-primary bg-primary/10"
                            : "border-border/40 hover:border-border"
                        )}
                      >
                        {theme.charAt(0).toUpperCase() + theme.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-3 block">Font Size</label>
                  <select
                    value={settings.appearance.fontSize}
                    onChange={(e) => setSettings({
                      ...settings,
                      appearance: { ...settings.appearance, fontSize: e.target.value }
                    })}
                    className="w-full px-4 py-2 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="rounded-xl border border-border/40 bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-6">Security</h2>
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-muted/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-medium text-sm">Two-Factor Authentication</p>
                    <span className="text-xs text-green-500 font-medium">Enabled</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Your account is protected with 2FA
                  </p>
                </div>
                <button className="w-full p-4 rounded-lg border border-border/40 hover:border-primary transition-colors text-left">
                  <p className="font-medium text-sm mb-1">Change Password</p>
                  <p className="text-xs text-muted-foreground">Update your password</p>
                </button>
                <button className="w-full p-4 rounded-lg border border-border/40 hover:border-primary transition-colors text-left">
                  <p className="font-medium text-sm mb-1">Active Sessions</p>
                  <p className="text-xs text-muted-foreground">Manage your active sessions</p>
                </button>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="rounded-xl border border-border/40 bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-6">API Keys</h2>
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-muted/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-medium text-sm">Groq API Key</p>
                    <span className="text-xs text-green-500 font-medium">Active</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="password"
                      value={settings.api.key}
                      readOnly
                      className="flex-1 px-3 py-2 rounded bg-background text-sm font-mono text-muted-foreground"
                    />
                    <button className="p-2 rounded hover:bg-accent transition-colors">
                      <Globe className="h-4 w-4 text-muted-foreground" />
                    </button>
                  </div>
                </div>
                <button className="w-full inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors border border-border/40 bg-background hover:bg-accent h-10">
                  <Key className="h-4 w-4 mr-2" />
                  Generate New Key
                </button>
              </div>
            </div>
          )}

          {/* Save Button */}
          <div className="mt-6 flex justify-end">
            <button className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-6">
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
