import { Project } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5179/api';

function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
}

export const fetchProjects = async (): Promise<Project[]> => {
  const res = await fetch(`${API_URL}/projects`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error('Failed to fetch projects');
  return res.json();
};

export const fetchProject = async (id: string): Promise<Project> => {
  const res = await fetch(`${API_URL}/projects/${id}`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error('Failed to fetch project');
  return res.json();
};

export const createProject = async (name: string, description: string): Promise<Project> => {
  const res = await fetch(`${API_URL}/projects`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ name, description })
  });
  if (!res.ok) throw new Error('Failed to create project');
  return res.json();
};

export const generateProject = async (id: string): Promise<void> => {
  const res = await fetch(`${API_URL}/projects/${id}/generate`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to start generation');
};

export const deleteProject = async (id: string): Promise<void> => {
  const res = await fetch(`${API_URL}/projects/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to delete project');
};

export const updateVersionStatus = async (projectId: string, versionId: string, status: string): Promise<void> => {
  const res = await fetch(`${API_URL}/projects/${projectId}/versions/${versionId}/status`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify({ status })
  });
  if (!res.ok) throw new Error('Failed to update status');
};

export const deleteVersion = async (projectId: string, versionId: string): Promise<void> => {
  const res = await fetch(`${API_URL}/projects/${projectId}/versions/${versionId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to delete version');
};
