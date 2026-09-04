import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchProject, updateVersionStatus, deleteVersion, generateProject } from '../api/client';
import { ChevronRight, RefreshCw, Trash2, Box, Download } from 'lucide-react';
import { useProjectLogs } from '../hooks/useProjectLogs';

export default function ProjectDetail() {
  const { id } = useParams<{id: string}>();
  const queryClient = useQueryClient();
  const logs = useProjectLogs(id || null);
  
  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => fetchProject(id!),
    refetchInterval: 5000, 
  });

  const statusMutation = useMutation({
    mutationFn: ({vid, status}: {vid: string, status: string}) => updateVersionStatus(id!, vid, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['project', id] })
  });

  const deleteMutation = useMutation({
    mutationFn: (vid: string) => deleteVersion(id!, vid),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['project', id] })
  });
  
  const retryMutation = useMutation({
    mutationFn: () => generateProject(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['project', id] })
  });

  if (isLoading) return <div className="p-8 text-sm text-gray-500">Loading workspace...</div>;
  if (!project) return <div className="p-8 text-sm text-gray-500">Project not found.</div>;

  return (
    <div className="space-y-6">
      <nav className="flex items-center text-sm font-medium text-gray-500 mb-2">
        <Link to="/" className="hover:text-gray-900 transition-colors">Designs</Link>
        <ChevronRight size={16} className="mx-2" />
        <span className="text-gray-900 truncate">{project.name}</span>
      </nav>
      
      <header className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="space-y-1.5 max-w-3xl w-full">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold leading-none tracking-tight text-gray-900">{project.name}</h1>
            <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${
                project.status === 'completed' ? 'border-transparent bg-gray-100 text-gray-900' :
                project.status === 'generating' ? 'border-transparent bg-blue-600 text-white' :
                project.status === 'failed' ? 'border-transparent bg-red-500 text-white' :
                'text-foreground'
            }`}>
              {project.status === 'generating' ? 'Generating' : project.status === 'completed' ? 'Completed' : project.status === 'failed' ? 'Failed' : project.status}
            </span>
          </div>
          <p className="text-sm text-gray-500">{project.description}</p>
          
          {project.llmPlan && project.llmPlan.includes('{') && (
            <div className="mt-4 pt-4 border-t border-gray-100">
               <h3 className="text-sm font-semibold text-gray-900 mb-2">Approved Build Plan</h3>
               <div className="bg-gray-50 rounded-md p-3 text-xs text-gray-700 font-mono overflow-x-auto border border-gray-200">
                 {(() => {
                   try {
                     const plan = JSON.parse(project.llmPlan);
                     if (plan.image_url) delete plan.image_url;
                     if (plan.image_prompt) delete plan.image_prompt;
                     return JSON.stringify(plan, null, 2);
                   } catch {
                     return project.llmPlan;
                   }
                 })()}
               </div>
            </div>
          )}
        </div>
        
        {(project.status === 'failed' || project.status === 'completed') && (
            <button 
                onClick={() => retryMutation.mutate()} 
                className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-gray-200 bg-white hover:bg-gray-100 hover:text-gray-900 h-10 px-4 py-2 shrink-0"
            >
                <RefreshCw size={16} aria-hidden="true"/> Iterate Generation
            </button>
        )}
      </header>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold tracking-tight text-gray-900">Iterations</h2>
        
        {project.status === 'generating' && (
            <div className="rounded-md border border-blue-200 bg-blue-50/50 p-4 text-sm text-blue-800 flex flex-col gap-3">
                <div className="flex items-center gap-3">
                    <RefreshCw className="animate-spin h-4 w-4" />
                    The autonomous agent is currently working in Fusion 360. This usually takes 60 seconds...
                </div>
                <div className="w-full bg-gray-900 rounded-md p-4 h-48 overflow-y-auto flex flex-col font-mono text-xs text-green-400 shadow-inner">
                    {logs.length === 0 && <span className="text-gray-500 italic">Waiting for agent logs...</span>}
                    {logs.map((log, idx) => <div key={idx}>$ {log}</div>)}
                </div>
            </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {project.versions?.map((v: any) => (
            <div key={v.id} className="rounded-xl border border-gray-200 bg-white text-gray-900 shadow-sm flex flex-col sm:flex-row overflow-hidden group">
               <div className="w-full sm:w-48 h-48 bg-gray-100 flex flex-col items-center justify-center relative shrink-0 border-r border-gray-200">
                  {v.imagePath ? (
                      <img src={(import.meta.env.VITE_API_URL || 'http://localhost:5045/api').replace('/api', '') + v.imagePath} alt="Preview" className="w-full h-full object-cover mix-blend-multiply" />
                  ) : (
                      <Box size={32} className="text-gray-400" />
                  )}
                  
                  {v.filePathSTL && (
                      <a href={`http://localhost:5045/temp/${v.filePathSTL.split('/').pop()}`} download
                         className="absolute inset-0 bg-gray-900/60 backdrop-blur-sm flex flex-col items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-all duration-200">
                          <Download size={24} className="mb-2"/>
                          <span className="font-medium text-sm">Download STL</span>
                      </a>
                  )}
               </div>

               <div className="p-6 flex-1 flex flex-col min-w-0">
                   <div className="flex justify-between items-start mb-4">
                     <h3 className="font-semibold leading-none tracking-tight text-lg">Attempt {v.versionNumber}</h3>
                     <button onClick={() => deleteMutation.mutate(v.id)} className="text-gray-400 hover:text-red-600 transition-colors">
                       <Trash2 size={16} />
                     </button>
                   </div>

                   <div className="space-y-4 flex-1 flex flex-col">
                      <div className="space-y-1.5">
                        <label className="text-xs font-medium leading-none text-gray-500 uppercase tracking-wider">Status</label>
                        <select 
                            className="flex h-9 w-full rounded-md border border-gray-300 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
                            value={v.status}
                            onChange={(e) => statusMutation.mutate({vid: v.id, status: e.target.value})}
                        >
                            <option value="no status">Unmarked</option>
                            <option value="viable option">Viable Option</option>
                            <option value="chosen">Final Choice</option>
                            <option value="archive">Archived</option>
                        </select>
                      </div>
                      
                      <div className="flex-1 space-y-1.5">
                         <label className="text-xs font-medium leading-none text-gray-500 uppercase tracking-wider">Agent Log</label>
                         <div className="text-xs text-gray-600 font-mono bg-gray-50 border border-gray-200 p-3 rounded-md max-h-[80px] overflow-y-auto whitespace-pre-wrap">
                             {v.agentLog || "No logs available."}
                         </div>
                      </div>
                   </div>
               </div>
            </div>
          ))}
          {(!project.versions || project.versions.length === 0) && project.status !== 'generating' && (
              <div className="col-span-full rounded-md border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500">
                  No iterations available yet.
              </div>
          )}
        </div>
      </div>
    </div>
  );
}
