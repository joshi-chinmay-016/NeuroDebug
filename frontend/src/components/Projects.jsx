import { motion } from 'framer-motion'
import { Plus, Folder, Trash2, Edit, Clock, MoreVertical } from 'lucide-react'
import { useState } from 'react'
import { cn } from '../lib/utils'

const mockProjects = [
  {
    id: 1,
    name: 'API Authentication Module',
    description: 'Debugging JWT token validation issues',
    lastModified: '2 hours ago',
    debugSessions: 5,
    status: 'active',
  },
  {
    id: 2,
    name: 'Data Processing Pipeline',
    description: 'Optimizing async data handling',
    lastModified: '1 day ago',
    debugSessions: 12,
    status: 'active',
  },
  {
    id: 3,
    name: 'UI Component Library',
    description: 'Fixing React component state issues',
    lastModified: '3 days ago',
    debugSessions: 8,
    status: 'archived',
  },
]

export default function Projects() {
  const [projects, setProjects] = useState(mockProjects)
  const [showNewProject, setShowNewProject] = useState(false)

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-between mb-8"
      >
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground mt-2">
            Organize and manage your debugging sessions
          </p>
        </div>
        <button
          onClick={() => setShowNewProject(true)}
          className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-4 py-2"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Project
        </button>
      </motion.div>

      {/* Projects Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {projects.map((project, index) => (
          <motion.div
            key={project.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className="group rounded-xl border border-border/40 bg-card p-6 shadow-sm hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 rounded-lg bg-primary/10">
                <Folder className="h-5 w-5 text-primary" />
              </div>
              <button className="p-2 rounded-md hover:bg-accent transition-colors opacity-0 group-hover:opacity-100">
                <MoreVertical className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>

            <h3 className="font-semibold mb-2">{project.name}</h3>
            <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
              {project.description}
            </p>

            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>{project.lastModified}</span>
              </div>
              <span>{project.debugSessions} sessions</span>
            </div>

            <div className="mt-4 pt-4 border-t border-border/40 flex gap-2">
              <button className="flex-1 inline-flex items-center justify-center rounded-md text-xs font-medium transition-colors bg-secondary text-secondary-foreground hover:bg-secondary/80 h-8">
                <Edit className="h-3 w-3 mr-1" />
                Edit
              </button>
              <button className="inline-flex items-center justify-center rounded-md text-xs font-medium transition-colors hover:bg-destructive/10 text-destructive h-8 px-3">
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Empty State */}
      {projects.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Folder className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No projects yet</h3>
          <p className="text-muted-foreground mb-4">
            Create your first project to start organizing your debugging sessions
          </p>
          <button
            onClick={() => setShowNewProject(true)}
            className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-4 py-2"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Project
          </button>
        </motion.div>
      )}

      {/* New Project Modal */}
      {showNewProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md rounded-xl border border-border/40 bg-card p-6 shadow-lg"
          >
            <h2 className="text-xl font-semibold mb-4">Create New Project</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Project Name</label>
                <input
                  type="text"
                  placeholder="Enter project name"
                  className="w-full px-3 py-2 rounded-md border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Description</label>
                <textarea
                  placeholder="Enter project description"
                  rows={3}
                  className="w-full px-3 py-2 rounded-md border border-border/40 bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowNewProject(false)}
                className="flex-1 inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors bg-secondary text-secondary-foreground hover:bg-secondary/80 h-10"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowNewProject(false)}
                className="flex-1 inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors bg-primary text-primary-foreground hover:bg-primary/90 h-10"
              >
                Create Project
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
