import { motion } from 'framer-motion'
import { User, Bell, Shield, Palette, Key, Save, Eye, EyeOff, RefreshCw } from 'lucide-react'
import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useNotification } from '../contexts/NotificationContext'
import profileService from '../services/profileService'
import apiClient from '../services/api'
import { cn } from '../lib/utils'

export default function Settings() {
  const { isAuthenticated, user, getAccessToken, logout } = useAuth()
  const { success, error: showError } = useNotification()
  const [activeTab, setActiveTab] = useState('profile')
  const [isLoading, setIsLoading] = useState(false)
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  
  const [profile, setProfile] = useState({
    display_name: '',
    email: '',
  })
  
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
  })

  // Add auth token to API requests
  useEffect(() => {
    const token = getAccessToken()
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }, [isAuthenticated, getAccessToken])

  // Load profile data
  const loadProfile = async () => {
    if (!isAuthenticated) return

    setIsLoading(true)
    try {
      const data = await profileService.getProfile()
      setProfile({
        display_name: data.display_name || '',
        email: data.email || '',
      })
    } catch (err) {
      showError('Failed to load profile')
      console.error('Failed to load profile:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadProfile()
  }, [isAuthenticated])

  const handleProfileUpdate = async () => {
    setIsLoading(true)
    try {
      await profileService.updateProfile({
        display_name: profile.display_name,
        email: profile.email,
      })
      success('Profile updated successfully')
    } catch (err) {
      showError('Failed to update profile')
      console.error('Failed to update profile:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handlePasswordChange = async () => {
    setIsLoading(true)
    try {
      await profileService.changePassword(passwordForm)
      success('Password changed successfully')
      setPasswordForm({ current_password: '', new_password: '' })
    } catch (err) {
      showError('Failed to change password. Please check your current password.')
      console.error('Failed to change password:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'api', label: 'API Keys', icon: Key },
  ]

  if (!isAuthenticated) {
    return (
      <div className="container py-8">
        <div className="text-center py-16">
          <p className="text-muted-foreground">Please sign in to access settings</p>
        </div>
      </div>
    )
  }

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
                  "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200",
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
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold">Profile Settings</h2>
                <button
                  onClick={loadProfile}
                  className="p-2 rounded-lg hover:bg-accent transition-colors"
                  title="Refresh"
                >
                  <RefreshCw className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>
              <div className="space-y-6">
                <div>
                  <label className="text-sm font-medium mb-2 block">Display Name</label>
                  <input
                    type="text"
                    value={profile.display_name}
                    onChange={(e) => setProfile({ ...profile, display_name: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    placeholder="Your display name"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Email</label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    placeholder="your@email.com"
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end">
                <button
                  onClick={handleProfileUpdate}
                  disabled={isLoading}
                  className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all duration-200 bg-gradient-to-r from-primary to-accent text-white hover:shadow-lg hover:shadow-primary/25 h-10 px-6 disabled:opacity-50"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="rounded-xl border border-border/40 bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-6">Notification Preferences</h2>
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">Notification settings coming soon</p>
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="rounded-xl border border-border/40 bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-6">Appearance</h2>
              <div className="space-y-6">
                <p className="text-sm text-muted-foreground">Appearance settings coming soon</p>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="rounded-xl border border-border/40 bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-6">Security</h2>
              <div className="space-y-6">
                <div>
                  <h3 className="font-medium text-sm mb-4">Change Password</h3>
                  <div className="space-y-4">
                    <div className="relative">
                      <label className="text-sm font-medium mb-2 block">Current Password</label>
                      <input
                        type={showCurrentPassword ? 'text' : 'password'}
                        value={passwordForm.current_password}
                        onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                        className="w-full px-4 py-2 pr-10 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="Enter current password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-8 text-muted-foreground hover:text-foreground"
                      >
                        {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    <div className="relative">
                      <label className="text-sm font-medium mb-2 block">New Password</label>
                      <input
                        type={showNewPassword ? 'text' : 'password'}
                        value={passwordForm.new_password}
                        onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                        className="w-full px-4 py-2 pr-10 rounded-lg border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="Enter new password (min 8 characters)"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-8 text-muted-foreground hover:text-foreground"
                      >
                        {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={handlePasswordChange}
                    disabled={isLoading || !passwordForm.current_password || !passwordForm.new_password}
                    className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all duration-200 bg-gradient-to-r from-primary to-accent text-white hover:shadow-lg hover:shadow-primary/25 h-10 px-6 disabled:opacity-50"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {isLoading ? 'Changing...' : 'Change Password'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="rounded-xl border border-border/40 bg-card p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-6">API Keys</h2>
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">API key management coming soon</p>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
