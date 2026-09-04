import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createProject, generateProject } from '../api/client';
import { ArrowRight, Bot } from 'lucide-react';

export default function NewProject() {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [step, setStep] = useState(1);
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handlePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const p = await createProject(name, description);
      setProject(p);
      setStep(2);
    } catch (e) {
      alert("Failed to create project");
    }
    setLoading(false);
  };

  const handleApprove = async () => {
    setLoading(true);
    try {
      await generateProject(project.id);
      navigate(`/project/${project.id}`);
    } catch (e) {
      alert("Failed to start generation");
    }
    setLoading(false);
  };

  return (
    <div className="max-w-2xl mx-auto p-6 mt-10 bg-white rounded-lg shadow-sm border border-gray-200">
      {step === 1 && (
        <form onSubmit={handlePlan}>
          <h2 className="text-2xl font-bold mb-6">Describe Your Item</h2>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
            <input required type="text" value={name} onChange={e => setName(e.target.value)}
              className="w-full border border-gray-300 rounded-md p-2" placeholder="e.g. Robot Chassis v2" />
          </div>
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea required value={description} onChange={e => setDescription(e.target.value)} rows={5}
              className="w-full border border-gray-300 rounded-md p-2" 
              placeholder="Describe the 3D model, sizes, connections..." />
          </div>
          <button disabled={loading} type="submit" 
            className="w-full bg-blue-600 text-white rounded-md p-3 font-medium hover:bg-blue-700 flex justify-center items-center gap-2">
            {loading ? 'Consulting LLM...' : 'Generate Plan'} <Bot size={20}/>
          </button>
        </form>
      )}

      {step === 2 && project && (
        <div>
          <h2 className="text-2xl font-bold mb-4">LLM Print Plan</h2>
          <div className="bg-gray-50 border rounded-md p-4 mb-6 whitespace-pre-wrap text-sm font-mono text-gray-700">
            {/* Real app would show the actual LLM plan from the database here.
                Because the python worker handles the LLM in Phase 4, we stub it visually here.
             */}
             Analysis complete. 
             Based on "{project.description}", the AI Agent is ready to attempt to generate this via Fusion 360 MCP.
             
             Click approve to dispatch the 10-attempt CAD worker.
          </div>
          <button disabled={loading} onClick={handleApprove}
            className="w-full bg-green-600 text-white rounded-md p-3 font-medium hover:bg-green-700 flex justify-center items-center gap-2">
            {loading ? 'Dispatching Agent...' : 'Approve & Start CAD Generation'} <ArrowRight size={20}/>
          </button>
        </div>
      )}
    </div>
  );
}
