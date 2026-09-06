import { useState, useEffect } from 'react';
import { Sparkles, AlertCircle } from 'lucide-react';
import LearningPathForm from './components/LearningPathForm';
import ProgressTracker from './components/ProgressTracker';
import LearningPathResult from './components/LearningPathResult';
import { generateLearningPath, checkTaskStatus, getTaskResult } from './lib/api';

function App() {
  const [stage, setStage] = useState('form'); // 'form', 'processing', 'result', 'error'
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Poll task status
  useEffect(() => {
    if (!taskId || stage !== 'processing') return;

    const pollInterval = setInterval(async () => {
      try {
        const statusData = await checkTaskStatus(taskId);
        setTaskStatus(statusData.status);

        if (statusData.status === 'finished') {
          clearInterval(pollInterval);
          // Fetch the result
          const resultData = await getTaskResult(taskId);
          setResult(resultData);
          setStage('result');
        } else if (statusData.status === 'failed') {
          clearInterval(pollInterval);
          setError(statusData.error || 'Task failed. Please try again.');
          setStage('error');
        }
      } catch (err) {
        console.error('Error polling status:', err);
        clearInterval(pollInterval);
        setError('Failed to check task status. Please try again.');
        setStage('error');
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(pollInterval);
  }, [taskId, stage]);

  const handleSubmit = async (formData) => {
    setError(null);
    setStage('processing');
    
    try {
      const response = await generateLearningPath(formData);
      setTaskId(response.task_id);
      setTaskStatus(response.status);
    } catch (err) {
      console.error('Error generating learning path:', err);
      setError(err.response?.data?.error || 'Failed to generate learning path. Please try again.');
      setStage('error');
    }
  };

  const handleReset = () => {
    setStage('form');
    setTaskId(null);
    setTaskStatus(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-12 h-12 text-white" />
            <h1 className="text-5xl font-bold text-white">
              AI Learning Path Generator
            </h1>
          </div>
          <p className="text-white/80 text-xl max-w-2xl mx-auto">
            Get personalized, AI-powered learning paths with real-time job market insights
          </p>
        </header>

        {/* Main Content */}
        <main>
          {stage === 'form' && (
            <div className="max-w-2xl mx-auto">
              <LearningPathForm onSubmit={handleSubmit} isLoading={false} />
            </div>
          )}

          {stage === 'processing' && (
            <div className="max-w-2xl mx-auto">
              <ProgressTracker status={taskStatus} error={null} />
            </div>
          )}

          {stage === 'result' && result && (
            <LearningPathResult data={result} onReset={handleReset} />
          )}

          {stage === 'error' && (
            <div className="max-w-2xl mx-auto">
              <div className="glass-card border-white/20 rounded-lg p-8 text-center">
                <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-white mb-2">
                  Something Went Wrong
                </h2>
                <p className="text-white/80 mb-6">
                  {error}
                </p>
                <button
                  onClick={handleReset}
                  className="px-6 py-3 bg-white text-purple-600 rounded-lg font-semibold hover:bg-white/90 transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="text-center mt-16 text-white/60">
          <p className="text-sm">
            Powered by AI • Built with React + Vite + Vercel
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;
