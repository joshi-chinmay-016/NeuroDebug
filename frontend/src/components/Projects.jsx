import { motion, AnimatePresence } from 'framer-motion'
import { FolderPlus, MoreVertical, Archive, Trash2, Clock, CheckCircle, AlertCircle, Search } from 'lucide-react'
import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import workspaceService from '../services/workspaceService'
import { useNotification } from '../contexts/NotificationContext'
import { CardSkeleton } from './Skeleton'

export default function Projects() {
  const { isAuthenticated } = useAuth()
  const { success, error: showError } = useNotification()
  const [projects, setProjects] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [menuOpen, setMenuOpen] = useState(null)

  const loadProjects = async () => {
    if (!isAuthenticated) return
    setIsLoading(true)
    try {
      const data = await workspaceService.getProjects()
      setProjects(data)
    } catch (err) {
      showError('Failed to load projects')
      console.error('Failed to load projects:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [isAuthenticated])

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return

    try {
      const project = await workspaceService.createProject(newProjectName)
      setProjects([...projects, project])
      setNewProjectName('')
      setShowCreateModal(false)
      success('Project created successfully')
    } catch (err) {
      showError('Failed to create project')
      console.error('Failed to create project:', err)
    }
  }

  const handleArchiveProject = async (projectId) => {
    try {
      await workspaceService.archiveProject(projectId)
      setProjects(projects.map(p => p.id === projectId ? { ...p, is_archived: true } : p))
      setMenuOpen(null)
      success('Project archived')
    } catch (err) {
      showError('Failed to archive project')
      console.error('Failed to archive project:', err)
    }
  }

  const handleDeleteProject = async (projectId) => {
    try {
      await workspaceService.deleteProject(projectId)
      setProjects(projects.filter(p => p.id !== projectId))
      setMenuOpen(null)
      success('Project deleted')
    } catch (err) {
      showError('Failed to delete project')
      console.error('Failed to delete project:', err)
    }
  }

  const handleRestoreProject = async (projectId) => {
    try {
      await workspaceService.restoreProject(projectId)
      setProjects(projects.map(p => p.id === projectId ? { ...p, is_archived: false } : p))
      setMenuOpen(null)
      success('Project restored')
    } catch (err) {
      showError('Failed to restore project')
      console.error('Failed to restore project:', err)
    }
  }

  const filteredProjects = projects.filter(p =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 100,
        damping: 12,
      },
    },
  }

  if (!isAuthenticated) {
    return (
      <div className="container py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center py-12"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          >
            <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          </motion.div>
          <h2 className="text-2xl font-semibold mb-2">Authentication Required</h2>
          <p className="text-muted-foreground">Please log in to access your projects.</p>
        </motion.div>
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
        <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
        <p className="text-muted-foreground mt-2">
          Manage your debugging projects and organize your work
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="flex items-center justify-between mb-6"
      >
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-4 py-2 rounded-lg border border-border/40 bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 w-64 transition-all"
          />
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
        >
          <FolderPlus className="h-4 w-4" />
          New Project
        </motion.button>
      </motion.div>

      {isLoading ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
        >
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </motion.div>
      ) : filteredProjects.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center py-12"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          >
            <FolderPlus className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          </motion.div>
          <h2 className="text-xl font-semibold mb-2">No projects yet</h2>
          <p className="text-muted-foreground mb-4">Create your first project to get started</p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <FolderPlus className="h-4 w-4" />
            Create Project
          </motion.button>
        </motion.div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
        >
          {filteredProjects.map((project) => (
            <motion.div
              key={project.id}
              variants={itemVariants}
              whileHover={{ scale: 1.02, y: -4 }}
              whileTap={{ scale: 0.98 }}
              className="relative rounded-xl border border-border/40 bg-card p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{project.name}</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {project.session_count || 0} sessions
                  </p>
                </div>
                <div className="relative">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => setMenuOpen(menuOpen === project.id ? null : project.id)}
                    className="p-1 rounded hover:bg-muted transition-colors"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </motion.button>
                  <AnimatePresence>
                    {menuOpen === project.id && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -10 }}
                        transition={{ duration: 0.15 }}
                        className="absolute right-0 top-8 w-48 bg-background border border-border/40 rounded-lg shadow-lg z-10 overflow-hidden"
                      >
                        {!project.is_archived ? (
                          <>
                            <motion.button
                              whileHover={{ x: 4 }}
                              onClick={() => handleArchiveProject(project.id)}
                              className="w-full px-4 py-2 text-left text-sm hover:bg-muted flex items-center gap-2 transition-colors"
                            >
                              <Archive className="h-4 w-4" />
                              Archive
                            </motion.button>
                            <motion.button
                              whileHover={{ x: 4 }}
                              onClick={() => handleDeleteProject(project.id)}
                              className="w-full px-4 py-2 text-left text-sm hover:bg-muted flex items-center gap-2 text-destructive transition-colors"
                            >
                              <Trash2 className="h-4 w-4" />
                              Delete
                            </motion.button>
                          </>
                        ) : (
                          <motion.button
                            whileHover={{ x: 4 }}
                            onClick={() => handleRestoreProject(project.id)}
                            className="w-full px-4 py-2 text-left text-sm hover:bg-muted flex items-center gap-2 transition-colors"
                          >
                            <CheckCircle className="h-4 w-4" />
                            Restore
                          </motion.button>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>Last updated {project.last_used_at ? new Date(project.last_used_at).toLocaleDateString() : 'Never'}</span>
              </div>
              {project.is_archived && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-3 inline-flex items-center gap-1 text-xs text-muted-foreground"
                >
                  <Archive className="h-3 w-3" />
                  Archived
                </motion.div>
              )}
            </motion.div>
          ))}
        </motion.div>
      )}

      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => {
              setShowCreateModal(false)
              setNewProjectName('')
            }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              transition={{ duration: 0.2 }}
              className="bg-background rounded-xl p-6 w-full max-w-md shadow-lg"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-xl font-semibold mb-4">Create New Project</h2>
              <input
                type="text"
                placeholder="Project name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                className="w-full px-4 py-2 rounded-lg border border-border/40 bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 mb-4 transition-all"
                autoFocus
              />
              <div className="flex justify-end gap-2">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setShowCreateModal(false)
                    setNewProjectName('')
                  }}
                  className="px-4 py-2 rounded-lg border border-border/40 hover:bg-muted transition-colors"
                >
                  Cancel
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleCreateProject}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                >
                  Create
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
