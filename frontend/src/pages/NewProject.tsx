import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createProject, generateProject, fetchProject, updateProjectPlan } from '../api/client';
import { ArrowRight, Bot, RefreshCw } from 'lucide-react';
import { useProjectLogs } from '../hooks/useProjectLogs';
import YAML from 'yaml';

export default function NewProject() {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [step, setStep] = useState(1);
  const [projectId, setProjectId] = useState<string | null>(null);
  
  const [yamlText, setYamlText] = useState<string>('');
  const logs = useProjectLogs(projectId);
  
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (data: {name: string, description: string}) => createProject(data.name, data.description),
    onSuccess: (project) => {
      setProjectId(project.id);
      setStep(2);
    }
  });

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId!),
    enabled: !!projectId,
    refetchInterval: (query) => {
      const data = query.state.data;
      return (data && data.status === 'planning') ? 2000 : false;
    }
  });

  useEffect(() => {
    if (project && project.status === 'planned' && !yamlText) {
      try {
        const p = JSON.parse(project.llmPlan);
        if (p.image_url) delete p.image_url;
        if (p.image_prompt) delete p.image_prompt;
        setYamlText(YAML.stringify(p));
      } catch (e) {
        setYamlText(YAML.stringify({ parts: [] }));
      }
    }
  }, [project, yamlText]);

  const handlePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({ name, description });
  };

  const handleApprove = async () => {
    if (!project) return;
    try {
      let finalJson = "{}";
      if (yamlText) {
        finalJson = JSON.stringify(YAML.parse(yamlText));
      }
      await updateProjectPlan(project.id, finalJson);
      await generateProject(project.id);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      navigate(`/project/${project.id}`);
    } catch (e) {
      alert("Invalid YAML or failed to start generation");
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-6">
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="flex flex-col space-y-1.5 p-6 border-b border-gray-100">
          <h3 className="font-semibold leading-none tracking-tight text-xl text-gray-900">
            {step === 1 ? 'Describe Your Design' : 'Review Design Plan'}
          </h3>
          <p className="text-sm text-gray-500">
            {step === 1 ? 'Enter the details of the CAD model you want the AI to generate.' : 'Review and edit the dimensional plan before dispatching the agent.'}
          </p>
        </div>
        
        <div className="p-6">
          {step === 1 && (
            <form onSubmit={handlePlan} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium leading-none text-gray-900">Project Name</label>
                <input 
                  required 
                  type="text" 
                  value={name} 
                  onChange={e => setName(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-gray-300 bg-transparent px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent" 
                  placeholder="e.g. Robot Chassis v2" 
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium leading-none text-gray-900">Description</label>
                <textarea 
                  required 
                  value={description} 
                  onChange={e => setDescription(e.target.value)} 
                  rows={5}
                  className="flex w-full rounded-md border border-gray-300 bg-transparent px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent min-h-[120px]" 
                  placeholder="Describe the 3D model, dimensions, features, and constraints..." 
                />
              </div>
              <div className="pt-2">
                <button 
                  disabled={createMutation.isPending} 
                  type="submit" 
                  className="inline-flex w-full items-center justify-center gap-2 rounded-md text-sm font-medium bg-blue-600 text-white hover:bg-blue-600/90 h-10 px-4 py-2 disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Consulting Agent...' : 'Generate Plan'} <Bot size={18}/>
                </button>
              </div>
            </form>
          )}

          {step === 2 && project && project.status === 'planning' && (
             <div className="flex flex-col items-center justify-center py-12 text-gray-500 w-full">
                 <RefreshCw className="animate-spin mb-4" size={32} />
                 <p className="font-medium">Generating build plan and concept image...</p>
                 <div className="mt-6 w-full max-w-lg bg-gray-900 rounded-md p-4 h-48 overflow-y-auto flex flex-col font-mono text-xs text-green-400 shadow-inner">
                    {logs.length === 0 && <span className="text-gray-500 italic">Waiting for agent logs...</span>}
                    {logs.map((log, idx) => <div key={idx}>$ {log}</div>)}
                 </div>
             </div>
          )}

          {step === 2 && project && project.status === 'planned' && (
            <div className="space-y-6">
              
              {(() => {
                try {
                  const origPlan = JSON.parse(project.llmPlan);
                  if (origPlan.image_url) {
                    return (
                      <div className="w-full max-w-sm mx-auto bg-gray-100 rounded-xl overflow-hidden border border-gray-200 shadow-inner">
                          <img src={(import.meta.env.VITE_API_URL || 'http://localhost:5045/api').replace('/api', '') + origPlan.image_url} alt="Concept" className="w-full h-auto object-cover" />
                      </div>
                    );
                  }
                } catch(e) {}
                return null;
              })()}
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-gray-900">Edit Plan Parameters</h4>
                    <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded">Units: Centimeters (cm)</span>
                </div>
                <p className="text-sm text-gray-500 mb-2">Adjust the dimensional arrays below. 1 unit = 1 cm.</p>
                <textarea
                  className="w-full h-80 rounded-md border border-gray-300 bg-gray-900 text-green-400 font-mono text-sm p-4 focus:outline-none focus:ring-2 focus:ring-blue-600 shadow-inner leading-relaxed"
                  value={yamlText}
                  onChange={(e) => setYamlText(e.target.value)}
                  spellCheck="false"
                />
              </div>

              <div className="pt-4 border-t border-gray-100">
                <button 
                  onClick={handleApprove}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-md text-sm font-medium bg-emerald-600 text-white hover:bg-emerald-600/90 h-10 px-4 py-2"
                >
                  Approve Plan & Start Generation <ArrowRight size={18}/>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
