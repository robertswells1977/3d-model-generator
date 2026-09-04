import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchProject, updateVersionStatus, deleteVersion, generateProject } from '../api/client';
import { ArrowLeft, Box, Download, Trash2, RefreshCw } from 'lucide-react';

export default function ProjectDetail() {
  const { id } = useParams<{id: string}>();
  const queryClient = useQueryClient();
  
  // 5-SECOND POLLING
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

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading project...</div>;
  if (!project) return <div className="p-8 text-center">Project not found.</div>;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <Link to="/" className="inline-flex items-center text-blue-600 hover:underline mb-6 font-medium">
        <ArrowLeft size={16} className="mr-1" /> Back to Dashboard
      </Link>
      
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <div className="flex justify-between items-start mb-4">
            <div>
                <h1 className="text-3xl font-bold text-gray-800">{project.name}</h1>
                <p className="text-gray-500 mt-1">{project.description}</p>
            </div>
            <div className="flex gap-2">
                <span className="px-3 py-1 bg-gray-100 rounded-full text-sm font-medium uppercase text-gray-700">
                {project.status}
                </span>
                {(project.status === 'failed' || project.status === 'completed') && (
                    <button onClick={() => retryMutation.mutate()} className="px-3 py-1 bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-full text-sm font-medium flex items-center gap-1">
                        <RefreshCw size={14}/> Retry Generation
                    </button>
                )}
            </div>
        </div>
      </div>

      <h2 className="text-2xl font-bold mb-4">Generated Versions</h2>
      
      {project.status === 'generating' && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 text-blue-800 rounded-md flex items-center gap-3">
              <RefreshCw className="animate-spin" size={20} />
              The autonomous agent is currently working on this model. Please wait...
          </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {project.versions?.map(v => (
          <div key={v.id} className="bg-white rounded-lg shadow border p-5">
             <div className="flex justify-between items-center mb-4">
               <h3 className="text-lg font-bold">Attempt {v.versionNumber}</h3>
               <div className="flex items-center gap-2">
                 <select 
                    className="border rounded p-1 text-sm bg-gray-50"
                    value={v.status}
                    onChange={(e) => statusMutation.mutate({vid: v.id, status: e.target.value})}
                 >
                    <option value="no status">No Status</option>
                    <option value="viable option">Viable Option</option>
                    <option value="chosen">Chosen</option>
                    <option value="archive">Archive</option>
                 </select>
                 <button onClick={() => deleteMutation.mutate(v.id)} className="text-red-400 hover:text-red-600 p-1">
                   <Trash2 size={16} />
                 </button>
               </div>
             </div>

             <div className="bg-gray-100 rounded h-64 mb-4 flex items-center justify-center relative group">
                {v.imagePath ? (
                    <img src={v.imagePath} alt="Preview" className="h-full object-contain" />
                ) : (
                    <Box size={48} className="text-gray-300" />
                )}
                {/* Download Overlay */}
                {v.filePathSTL && (
                    <a href={`http://localhost:5045/temp/${v.filePathSTL.split('/').pop()}`} download
                       className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity rounded">
                        <Download size={32} className="mb-2"/>
                        <span className="font-medium">Download STL</span>
                    </a>
                )}
             </div>
             
             <div className="text-xs text-gray-500 font-mono bg-gray-50 p-2 rounded">
                 {v.agentLog || "No logs available."}
             </div>
          </div>
        ))}
        {(!project.versions || project.versions.length === 0) && project.status !== 'generating' && (
            <div className="col-span-full py-12 text-center text-gray-500">
                No versions generated yet.
            </div>
        )}
      </div>
    </div>
  );
}
