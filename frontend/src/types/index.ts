export interface User {
  id: string;
  name: string;
  email: string;
}

export interface ProjectVersion {
  id: string;
  projectId: string;
  versionNumber: number;
  status: string;
  filePathSTL?: string;
  filePathF3D?: string;
  imagePath?: string;
  agentLog?: string;
  createdAt: string;
}

export interface Project {
  id: string;
  userId: string;
  name: string;
  description: string;
  llmPlan: string;
  status: string;
  createdAt: string;
  versions: ProjectVersion[];
}
