import { useState } from 'react';
import { 
  BookOpen, 
  Clock, 
  Target, 
  TrendingUp, 
  Briefcase, 
  DollarSign,
  Users,
  Calendar,
  Download,
  ChevronDown,
  ChevronUp,
  ExternalLink
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { saveLearningPath, trackMilestone } from '../lib/api';

export default function LearningPathResult({ data, onReset }) {
  const [expandedMilestones, setExpandedMilestones] = useState([0]); // First milestone expanded by default
  const [savedPathId, setSavedPathId] = useState(data?.id || null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [completion, setCompletion] = useState({}); // { [index]: boolean }

  const toggleMilestone = (index) => {
    setExpandedMilestones(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setSaveMessage('');
      const resp = await saveLearningPath(data);
      if (resp?.success) {
        setSavedPathId(resp.path_id);
        setSaveMessage('Saved to your account.');
      } else {
        setSaveMessage('Save failed. Please login and try again.');
      }
    } catch (e) {
      setSaveMessage('Save failed. Are you logged in?');
    } finally {
      setSaving(false);
    }
  };

  const toggleCompletion = async (index) => {
    const next = !completion[index];
    setCompletion((prev) => ({ ...prev, [index]: next }));
    // Only attempt server update if we have a saved path id
    if (!savedPathId) return;
    try {
      await trackMilestone(savedPathId, index, next);
    } catch (e) {
      // revert on error
      setCompletion((prev) => ({ ...prev, [index]: !next }));
    }
  };

  const displayText = (r) => r?.title || r?.description || r?.url;

  const downloadJSON = () => {
    const dataStr = JSON.stringify(data, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `learning-path-${data.topic.replace(/\s+/g, '-').toLowerCase()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Card */}
      <Card className="glass-card border-white/20">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-3xl font-bold text-white mb-2">
                {data.title || `${data.topic} Learning Path`}
              </CardTitle>
              <CardDescription className="text-white/80 text-base">
                {data.description}
              </CardDescription>
              {saveMessage && (
                <div className="mt-2 text-sm text-white/80">{saveMessage}</div>
              )}
            </div>
            <div className="flex gap-2">
              <Button
                variant="glass"
                size="sm"
                onClick={handleSave}
                disabled={saving}
                className="gap-2"
              >
                {saving ? 'Saving…' : (savedPathId ? 'Save (Update)' : 'Save Path')}
              </Button>
              <Button
                variant="glass"
                size="sm"
                onClick={downloadJSON}
                className="gap-2"
              >
                <Download className="w-4 h-4" />
                Export
              </Button>
              <Button
                variant="glass"
                size="sm"
                onClick={onReset}
              >
                Create New
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/10 rounded-lg p-4">
              <Clock className="w-5 h-5 text-white/80 mb-2" />
              <p className="text-white/60 text-sm">Total Time</p>
              <p className="text-white font-semibold">{data.total_hours || 0} hours</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <Calendar className="w-5 h-5 text-white/80 mb-2" />
              <p className="text-white/60 text-sm">Duration</p>
              <p className="text-white font-semibold">{data.duration_weeks || 0} weeks</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <TrendingUp className="w-5 h-5 text-white/80 mb-2" />
              <p className="text-white/60 text-sm">Level</p>
              <p className="text-white font-semibold capitalize">{data.expertise_level}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <Target className="w-5 h-5 text-white/80 mb-2" />
              <p className="text-white/60 text-sm">Milestones</p>
              <p className="text-white font-semibold">{data.milestones?.length || 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Job Market Insights */}
      {data.job_market_data && (
        <Card className="glass-card border-white/20">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-white flex items-center gap-2">
              <Briefcase className="w-6 h-6" />
              Job Market Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {data.job_market_data.average_salary && (
                <div className="bg-white/10 rounded-lg p-4">
                  <DollarSign className="w-5 h-5 text-green-400 mb-2" />
                  <p className="text-white/60 text-sm">Average Salary</p>
                  <p className="text-white font-semibold">{data.job_market_data.average_salary}</p>
                </div>
              )}
              {data.job_market_data.open_positions && (
                <div className="bg-white/10 rounded-lg p-4">
                  <Users className="w-5 h-5 text-blue-400 mb-2" />
                  <p className="text-white/60 text-sm">Open Positions</p>
                  <p className="text-white font-semibold">{data.job_market_data.open_positions}</p>
                </div>
              )}
              {data.job_market_data.region && (
                <div className="bg-white/10 rounded-lg p-4">
                  <TrendingUp className="w-5 h-5 text-purple-400 mb-2" />
                  <p className="text-white/60 text-sm">Region</p>
                  <p className="text-white font-semibold">{data.job_market_data.region}</p>
                </div>
              )}
            </div>

            {/* Related Roles */}
            {data.job_market_data.related_roles && data.job_market_data.related_roles.length > 0 && (
              <div className="mt-4">
                <p className="text-white/80 font-medium mb-2">Related Career Paths:</p>
                <div className="flex flex-wrap gap-2">
                  {data.job_market_data.related_roles.slice(0, 6).map((role, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-white/10 rounded-full text-white text-sm"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Schedule */}
      {data.schedule && (
        <Card className="glass-card border-white/20">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-white flex items-center gap-2">
              <Calendar className="w-6 h-6" />
              Your Schedule
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-white/60 text-sm">Start Date</p>
                <p className="text-white font-semibold">{data.schedule.start_date}</p>
              </div>
              <div>
                <p className="text-white/60 text-sm">End Date</p>
                <p className="text-white font-semibold">{data.schedule.end_date}</p>
              </div>
              <div>
                <p className="text-white/60 text-sm">Hours per Week</p>
                <p className="text-white font-semibold">{data.schedule.hours_per_week} hours</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Milestones */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <BookOpen className="w-6 h-6" />
          Learning Milestones
        </h2>
        {data.milestones && data.milestones.map((milestone, index) => (
          <Card key={index} className="glass-card border-white/20">
            <CardHeader 
              className="cursor-pointer hover:bg-white/5 transition-colors"
              onClick={() => toggleMilestone(index)}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <CardTitle className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                    <span className="bg-white/20 rounded-full w-8 h-8 flex items-center justify-center text-sm">
                      {index + 1}
                    </span>
                    {milestone.title}
                  </CardTitle>
                  <CardDescription className="text-white/70">
                    {milestone.description}
                  </CardDescription>
                  <div className="mt-2 text-white/60 text-sm">
                    ⏱️ Estimated: {milestone.estimated_hours} hours
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="glass"
                    size="sm"
                    onClick={(e) => { e.stopPropagation(); toggleCompletion(index); }}
                  >
                    {completion[index] ? 'Completed' : 'Mark Complete'}
                  </Button>
                
                {expandedMilestones.includes(index) ? (
                  <ChevronUp className="w-5 h-5 text-white/60" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-white/60" />
                )}
                </div>
              </div>
            </CardHeader>
            
            {expandedMilestones.includes(index) && (
              <CardContent className="space-y-4 animate-fade-in">
                {/* Skills */}
                {milestone.skills_gained && milestone.skills_gained.length > 0 && (
                  <div>
                    <p className="text-white/80 font-medium mb-2">Skills You'll Gain:</p>
                    <div className="flex flex-wrap gap-2">
                      {milestone.skills_gained.map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-green-500/20 border border-green-500/30 rounded-full text-white text-sm"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Resources */}
                {milestone.resources && milestone.resources.length > 0 && (
                  <div>
                    <p className="text-white/80 font-medium mb-2">Learning Resources:</p>
                    <div className="space-y-2">
                      {milestone.resources.map((resource, idx) => (
                        <a
                          key={idx}
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-start gap-3 p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors group"
                        >
                          <ExternalLink className="w-4 h-4 text-white/60 mt-1 group-hover:text-white" />
                          <div className="flex-1">
                            <p className="text-white font-medium group-hover:underline">
                              {displayText(resource)}
                            </p>
                            {resource.description && resource.description !== resource.title && (
                              <p className="text-white/60 text-sm mt-1">{resource.description}</p>
                            )}
                            <p className="text-white/40 text-xs mt-1">
                              {resource.type}{resource.provider ? ` • ${resource.provider}` : ''}
                            </p>
                          </div>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
