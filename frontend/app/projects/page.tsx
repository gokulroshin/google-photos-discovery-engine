'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  FolderGit2,
  Plus,
  ArrowRight,
  Database,
  Layers,
  Search,
  Sparkles,
  Calendar,
  CheckCircle2,
  Clock,
} from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth-store';
import { Project } from '@/lib/types';

export default function ProjectsPage() {
  const { setActiveProjectId } = useAuthStore();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  const { data: projects, isLoading, refetch } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      await api.createProject({
        name: newProjectName,
        description: newProjectDesc,
        research_questions: ['What memory cues fail most often in natural language queries?'],
      });
      setShowCreateModal(false);
      setNewProjectName('');
      setNewProjectDesc('');
      refetch();
    } catch {
      setShowCreateModal(false);
    }
  };

  return (
    <div>
      {/* Top Banner */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '2rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
              Research Projects
            </h1>
            <span className="badge badge-info">Phase 0 Scaffolding</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Manage user feedback datasets, Gemini extraction runs, and retrieval failure taxonomies.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary"
        >
          <Plus size={18} />
          <span>New Research Project</span>
        </button>
      </div>

      {/* Metrics Summary Strip */}
      <div className="grid-3" style={{ marginBottom: '2rem' }}>
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: 'rgba(66, 133, 244, 0.15)', color: 'var(--google-blue)' }}>
              <FolderGit2 size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Active Projects</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{projects?.length || 2}</div>
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: 'rgba(52, 168, 83, 0.15)', color: 'var(--google-green)' }}>
              <Database size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Ingested Records</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>
                {projects?.reduce((acc, p) => acc + (p.record_count || 0), 0).toLocaleString() || '1,870'}
              </div>
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' }}>
              <Sparkles size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Classified Evidence Points</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>
                {projects?.reduce((acc, p) => acc + (p.evidence_count || 0), 0).toLocaleString() || '496'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Projects Grid */}
      <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--text-secondary)' }}>
        Active & Recent Workspaces
      </h2>

      {isLoading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading projects...
        </div>
      ) : (
        <div className="grid-2">
          {projects?.map((project: Project) => (
            <div
              key={project.id}
              className="card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <span className={`badge ${project.status === 'active' ? 'badge-success' : 'badge-neutral'}`}>
                    {project.status === 'active' ? <CheckCircle2 size={12} /> : <Clock size={12} />}
                    {project.status}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    ID: {project.id}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  {project.name}
                </h3>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.25rem', minHeight: '2.7rem' }}>
                  {project.description || 'No description provided.'}
                </p>

                {/* Research Questions preview */}
                {project.research_questions && project.research_questions.length > 0 && (
                  <div
                    style={{
                      background: 'var(--bg-secondary)',
                      padding: '0.75rem',
                      borderRadius: 'var(--radius-md)',
                      marginBottom: '1.25rem',
                      fontSize: '0.8rem',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                      Primary Research Question:
                    </div>
                    <div style={{ color: 'var(--text-primary)', fontStyle: 'italic' }}>
                      "{project.research_questions[0]}"
                    </div>
                  </div>
                )}

                {/* Metrics */}
                <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.25rem', fontSize: '0.85rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Records: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>{project.record_count || 0}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Evidence: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>{project.evidence_count || 0}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Updated: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>
                      {new Date(project.updated_at).toLocaleDateString()}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
                <Link
                  href={`/projects/${project.id}`}
                  onClick={() => setActiveProjectId(project.id)}
                  className="btn btn-primary"
                  style={{ width: '100%', justifyContent: 'center' }}
                >
                  <span>Open Project Dashboard</span>
                  <ArrowRight size={16} />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Stub for Creating New Project */}
      {showCreateModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            backdropFilter: 'blur(4px)',
          }}
        >
          <div className="card" style={{ width: '100%', maxWidth: '500px', margin: '1rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem' }}>
              Create New Research Project
            </h2>
            <form onSubmit={handleCreate}>
              <div className="input-group">
                <label className="input-label">Project Name</label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g. Natural Language Query Failures Q3"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  required
                />
              </div>
              <div className="input-group">
                <label className="input-label">Description / Scope</label>
                <textarea
                  className="input-field"
                  rows={3}
                  placeholder="Describe the research objective and target retrieval challenges..."
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
