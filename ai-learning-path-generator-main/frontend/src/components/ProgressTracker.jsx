import { useEffect, useState } from 'react';
import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';

const STATUS_MESSAGES = {
  queued: 'Task queued and waiting for worker...',
  started: 'AI is analyzing your learning requirements...',
  processing: 'Generating personalized curriculum...',
  researching: 'Finding the best learning resources...',
  analyzing: 'Analyzing job market trends...',
  finalizing: 'Finalizing your learning path...',
  finished: 'Learning path ready!',
  failed: 'Something went wrong. Please try again.',
};

const PROGRESS_STAGES = [
  { key: 'queued', label: 'Queued', progress: 10 },
  { key: 'started', label: 'Started', progress: 20 },
  { key: 'processing', label: 'Processing', progress: 50 },
  { key: 'analyzing', label: 'Analyzing', progress: 80 },
  { key: 'finished', label: 'Completed', progress: 100 },
];

export default function ProgressTracker({ status, error }) {
  const [currentProgress, setCurrentProgress] = useState(0);
  const [displayMessage, setDisplayMessage] = useState('');

  useEffect(() => {
    if (!status) return;

    // Find progress based on status
    const stage = PROGRESS_STAGES.find(s => s.key === status);
    if (stage) {
      setCurrentProgress(stage.progress);
    }

    // Set display message
    setDisplayMessage(STATUS_MESSAGES[status] || 'Processing...');
  }, [status]);

  const getStatusIcon = (status) => {
    if (status === 'failed') {
      return <AlertCircle className="w-6 h-6 text-red-400" />;
    }
    if (status === 'finished') {
      return <CheckCircle2 className="w-6 h-6 text-green-400" />;
    }
    return <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />;
  };

  return (
    <Card className="glass-card border-white/20">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-white flex items-center gap-3">
          {getStatusIcon(status)}
          Generating Your Learning Path
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <Progress 
            value={currentProgress} 
            className="h-3 bg-white/10"
          />
          <p className="text-white/80 text-sm text-center">
            {currentProgress}% Complete
          </p>
        </div>

        {/* Status Message */}
        <div className="text-center">
          <p className="text-white text-lg font-medium">
            {displayMessage}
          </p>
          {error && (
            <p className="text-red-300 mt-2 text-sm">
              Error: {error}
            </p>
          )}
        </div>

        {/* Stage Indicators */}
        <div className="space-y-2">
          {PROGRESS_STAGES.map((stage, index) => {
            const isActive = status === stage.key;
            const isComplete = currentProgress >= stage.progress;
            
            return (
              <div
                key={stage.key}
                className={`flex items-center gap-3 p-2 rounded-lg transition-all ${
                  isActive ? 'bg-white/10' : ''
                }`}
              >
                {isComplete ? (
                  <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                ) : isActive ? (
                  <Loader2 className="w-5 h-5 text-blue-400 animate-spin flex-shrink-0" />
                ) : (
                  <Circle className="w-5 h-5 text-white/30 flex-shrink-0" />
                )}
                <span className={`text-sm ${
                  isComplete || isActive ? 'text-white font-medium' : 'text-white/50'
                }`}>
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Estimated Time */}
        {status !== 'finished' && status !== 'failed' && (
          <div className="text-center pt-4 border-t border-white/10">
            <p className="text-white/60 text-sm">
              ⏱️ This usually takes 20-60 seconds
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
