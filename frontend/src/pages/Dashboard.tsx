import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchProjects, deleteProject } from '../api/client';
import { Link } from 'react-router-dom';
import { PlusCircle, Trash2, Box } from 'lucide-react';

export default function Dashboard() {
  const queryClient = useQueryClient();
  const { data: projects, isLoading } = useQuery({ queryKey: ['projects'], queryFn: fetchProjects });

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] })
  });

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading projects...</div>;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Your 3D Projects</h1>
        <Link to="/new" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center gap-2">
          <PlusCircle size={20} />
          New Design
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects?.map(p => (
          <div key={p.id} className="bg-white rounded-lg shadow border p-5 flex flex-col relative overflow-hidden">
            {p.status === 'generating' && (
               <div className="absolute top-0 left-0 w-full h-1 bg-blue-500 animate-pulse"></div>
            )}
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-semibold">{p.name}</h2>
              <button onClick={() => deleteMutation.mutate(p.id)} className="text-red-400 hover:text-red-600">
                <Trash2 size={18} />
              </button>
            </div>
            
            {/* Quick Image View */}
            <div className="bg-gray-100 rounded-md h-40 mb-4 flex items-center justify-center">
               {p.versions && p.versions.length > 0 && p.versions[0].imagePath ? (
                  <img src={p.versions[0].imagePath} alt="preview" className="h-full object-contain" />
               ) : (
                  <Box size={48} className="text-gray-300" />
               )}
            </div>

            <div className="text-sm text-gray-500 line-clamp-2 mb-4">{p.description}</div>
            
            <div className="mt-auto flex justify-between items-center">
              <span className={`px-2 py-1 rounded text-xs font-medium uppercase ${
                p.status === 'completed' ? 'bg-green-100 text-green-700' :
                p.status === 'generating' ? 'bg-blue-100 text-blue-700' :
                p.status === 'failed' ? 'bg-red-100 text-red-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {p.status}
              </span>
              <Link to={`/project/${p.id}`} className="text-blue-600 hover:underline text-sm font-medium">
                View Details
              </Link>
            </div>
          </div>
        ))}
        {projects?.length === 0 && (
          <div className="col-span-full text-center py-12 text-gray-500">
            No projects found. Create a new design!
          </div>
        )}
      </div>
    </div>
  );
}
