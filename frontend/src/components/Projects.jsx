import React, { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { FolderGit2, Plus, ArrowRight, Search, X, Trash2, CheckCircle2, AlertCircle, Lock, ShieldCheck } from 'lucide-react'
import StatusDot from './StatusDot'
import workspaceService from '../services/workspaceService'
import { useAuth } from '../contexts/AuthContext'

export default function Projects() {
  const { isAuthenticated } = useAuth()
  const [isCreating, setIsCreating] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [projectDesc, setProjectDesc] = useState('')
  const [search, setSearch] = useState('')
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadProjects = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      const data = await workspaceService.listProjects(0, 50)
      if (data && Array.isArray(data)) {
        setProjects(data)
      }
    } catch (err) {
      console.warn('Could not load projects:', err)
      setError('Unable to load projects from server')
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated])

  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  const handleCreateProject = async (e) => {
    e.preventDefault()
    if (!isAuthenticated || !projectName.trim()) return

    try {
      const created = await workspaceService.createProject(projectName.trim(), projectDesc.trim())
      setProjects([created, ...projects])
      setProjectName('')
      setProjectDesc('')
      setIsCreating(false)
    } catch (err) {
      console.error('Error creating project:', err)
      setError(err.message || 'Failed to create project')
    }
  }

  const handleDeleteProject = async (id) => {
    try {
      await workspaceService.archiveProject(id)
      setProjects(projects.filter((p) => p.id !== id))
    } catch (err) {
      console.error('Error archiving project:', err)
    }
  }

  const filteredProjects = projects.filter((p) =>
    (p.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (p.description || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-8">
      {/* Top bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display font-bold text-2xl text-[var(--ink)] tracking-tight">
            Developer Projects
          </h1>
          <p className="text-xs font-mono text-[var(--dim)] mt-1">
            Organize debugging sessions, codebase snippets, and verification workspaces
          </p>
        </div>

        {isAuthenticated && (
          <button
            onClick={() => setIsCreating(!isCreating)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--ink)] text-[var(--bg)] font-display font-bold text-xs hover:bg-white transition-all duration-150 shadow-sm"
          >
            {isCreating ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
            <span>{isCreating ? 'Cancel' : 'New Project'}</span>
          </button>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-[var(--red)]/10 border border-[var(--red)]/20 text-[var(--red)] text-xs font-mono">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Guest Lock Banner */}
      {!isAuthenticated && (
        <div className="card-hover rounded-2xl p-8 border border-[var(--line)] bg-[var(--surface-1)] space-y-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--green)]/15 border border-[var(--green)]/30 flex items-center justify-center">
              <Lock className="w-5 h-5 text-[var(--green)]" />
            </div>
            <div>
              <h3 className="font-display font-bold text-base text-[var(--ink)]">
                Project Workspaces Require an Account
              </h3>
              <p className="text-xs font-mono text-[var(--dim)] mt-0.5">
                Guest sessions cannot create persistent workspaces. Create a free account to organize codebases and save sessions.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono">
              <div className="font-bold text-[var(--ink)] mb-1">5 Daily Verifications</div>
              <div className="text-[var(--dim)]">Upgraded from 1 request/day guest limit</div>
            </div>
            <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono">
              <div className="font-bold text-[var(--ink)] mb-1">Isolated Workspaces</div>
              <div className="text-[var(--dim)]">Multi-file project grouping and tags</div>
            </div>
            <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono">
              <div className="font-bold text-[var(--ink)] mb-1">Full Audit Replay</div>
              <div className="text-[var(--dim)]">Revisit past diffs and execution evidence</div>
            </div>
          </div>

          <div className="pt-2 flex items-center gap-3">
            <Link
              to="/register"
              className="px-5 py-2.5 rounded-lg bg-[var(--ink)] text-[var(--bg)] font-display font-bold text-xs hover:bg-white transition-all flex items-center gap-2"
            >
              <span>Create Free Account</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>

            <Link
              to="/login"
              className="px-4 py-2.5 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] hover:border-[var(--border-strong)] transition-all"
            >
              <span>Sign In</span>
            </Link>
          </div>
        </div>
      )}

      {/* Inline Form Expansion (Authenticated Only) */}
      {isAuthenticated && isCreating && (
        <form
          onSubmit={handleCreateProject}
          className="card-hover rounded-xl p-6 border-l-4 border-l-[var(--green)] space-y-4 page-enter"
        >
          <div className="flex items-center justify-between">
            <h3 className="font-display font-bold text-sm text-[var(--ink)]">
              Create New Workspace Project
            </h3>
            <span className="text-[11px] font-mono text-[var(--dim)]">
              Secure Isolated Tenant
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-mono text-[var(--dim)] mb-1">
                Project Name
              </label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g., Auth & Security Gateway"
                required
                className="w-full px-3 py-2 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] focus:outline-none focus:border-[var(--border-strong)]"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-[var(--dim)] mb-1">
                Description (Optional)
              </label>
              <textarea
                value={projectDesc}
                onChange={(e) => setProjectDesc(e.target.value)}
                placeholder="Brief summary of codebase scope..."
                rows={2}
                className="w-full px-3 py-2 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] focus:outline-none focus:border-[var(--border-strong)] resize-none"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsCreating(false)}
              className="px-3.5 py-1.5 rounded-lg text-xs font-mono text-[var(--dim)] hover:text-[var(--ink)]"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 rounded-lg bg-[var(--ink)] text-[var(--bg)] font-display font-bold text-xs hover:bg-white transition-all"
            >
              Save Project
            </button>
          </div>
        </form>
      )}

      {/* Authenticated Projects View */}
      {isAuthenticated && (
        <>
          {/* Search Input */}
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter projects by title or description..."
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-[var(--surface-1)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] placeholder-[var(--dim)] focus:outline-none focus:border-[var(--border-strong)]"
            />
            <Search className="w-4 h-4 text-[var(--dim)] absolute left-3 top-2.5" />
          </div>

          {/* Project Cards Grid */}
          {loading ? (
            <div className="p-8 text-center font-mono text-xs text-[var(--dim)] animate-pulse">
              Loading workspace projects...
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="p-8 text-center font-mono text-xs text-[var(--dim)] bg-[var(--surface-1)] border border-[var(--line)] rounded-xl">
              No projects found. Click "New Project" to create your first workspace.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {filteredProjects.map((proj) => (
                <div
                  key={proj.id}
                  className="card-hover rounded-xl p-5 flex flex-col justify-between space-y-4 group"
                >
                  <div>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] flex items-center justify-center">
                          <FolderGit2 className="w-4 h-4 text-[var(--ink)]" />
                        </div>
                        <div>
                          <h3 className="font-display font-bold text-sm text-[var(--ink)] group-hover:text-white transition-colors">
                            {proj.name}
                          </h3>
                          <span className="text-[10px] font-mono text-[var(--dim)]">
                            Created {new Date(proj.created_at || Date.now()).toLocaleDateString()}
                          </span>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDeleteProject(proj.id)}
                        className="text-[var(--dim)] hover:text-[var(--red)] transition-colors p-1"
                        title="Archive Project"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <p className="text-xs text-[var(--dim)] font-mono mt-3 leading-relaxed">
                      {proj.description || 'No description provided.'}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-[var(--line)] flex items-center justify-between text-xs font-mono text-[var(--dim)]">
                    <span>UUID: {proj.id.slice(0, 8)}...</span>
                    <span className="text-[var(--green)]">Active Workspace</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
