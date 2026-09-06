import { useState, useEffect, useMemo } from 'react';
import {
  Sparkles,
  LayoutGrid,
  Clock,
  Target,
  TrendingUp,
  Wand2,
  GraduationCap,
  BookOpen,
  Rocket
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from './components/ui/select';
import ProgressTracker from './components/ProgressTracker';
import LearningPathResult from './components/LearningPathResult';
import { generateLearningPath, checkTaskStatus, getTaskResult, API_BASE_URL } from './lib/api.js';

const CATEGORY_TOPICS = {
  programming: [
    'Python',
    'JavaScript',
    'React.js',
    'Web Development',
    'Go',
    'TypeScript'
  ],
  data: [
    'Machine Learning',
    'Deep Learning',
    'Data Analysis',
    'Natural Language Processing',
    'Computer Vision',
    'SQL'
  ],
  design: [
    'UI/UX Design',
    'Product Design',
    '3D Modeling',
    'Visual Storytelling',
    'Design Systems'
  ],
  business: [
    'Product Management',
    'Growth Marketing',
    'Entrepreneurship',
    'Finance',
    'Leadership'
  ],
  ai_skills_roles: [
    'Prompt Engineering',
    'LLM Operations',
    'AI Product Manager',
    'AI Ethics',
    'Multimodal AI'
  ],
  other: [
    'Digital Marketing',
    'Creative Writing',
    'Photography',
    'Video Editing',
    'Technical Writing'
  ]
};

const DEFAULT_FORM = {
  topic: '',
  expertise_level: 'beginner',
  duration_weeks: 4,
  time_commitment: 'moderate',
  goals: ''
};

const MOCK_PATH = {
  title: 'Mock Path: Introduction to Mocking Data',
  description:
    'A playful path to help developers experiment with the UI without hitting the backend.',
  topic: 'mock_path',
  expertise_level: 'Beginner',
  milestones: [
    {
      title: 'Week 1: Understanding Mocks',
      description:
        'Learn what mocks are and why they are essential for frontend development.',
      duration_weeks: 1,
      resources: [
        {
          title: 'Article: What is Mocking?',
          url: '#',
          resource_type: 'article'
        },
        {
          title: 'Video: Mocking APIs with Postman',
          url: '#',
          resource_type: 'video'
        }
      ]
    },
    {
      title: 'Week 2: Creating Mock Data Structures',
      description: 'Practice creating realistic JSON data structures for your learning path.',
      duration_weeks: 1,
      resources: [
        {
          title: 'Tutorial: Building a Mock JSON Server',
          url: '#',
          resource_type: 'tutorial'
        },
        {
          title: 'Tool: Online JSON Formatter',
          url: '#',
          resource_type: 'tool'
        }
      ]
    }
  ],
  job_market: {
    demand_rating: 'Medium',
    salary_range: '$70k - $95k'
  }
};

function LegacyExperience() {
  const [formData, setFormData] = useState(DEFAULT_FORM);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [stage, setStage] = useState('form');
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const topicSuggestions = useMemo(() => {
    if (!selectedCategory) return [];
    return CATEGORY_TOPICS[selectedCategory] ?? [];
  }, [selectedCategory]);

  useEffect(() => {
    if (!taskId || stage !== 'processing') {
      return undefined;
    }

    const pollInterval = setInterval(async () => {
      try {
        const statusData = await checkTaskStatus(taskId);
        setTaskStatus(statusData.status);

        if (statusData.status === 'finished') {
          clearInterval(pollInterval);
          const resultData = await getTaskResult(taskId);
          setResult(resultData);
          setStage('result');
          setIsLoading(false);
        } else if (statusData.status === 'failed') {
          clearInterval(pollInterval);
          setError(statusData.error || 'Task failed. Please try again.');
          setStage('error');
          setIsLoading(false);
        }
      } catch (pollError) {
        console.error('Error polling status:', pollError);
        clearInterval(pollInterval);
        setError('Failed to check task status. Please try again.');
        setStage('error');
        setIsLoading(false);
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [taskId, stage]);

  const handleFormChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const appendTopic = (value) => {
    setFormData((prev) => {
      const segments = prev.topic
        .split(',')
        .map((entry) => entry.trim())
        .filter(Boolean);

      if (segments.includes(value)) {
        return prev;
      }

      const nextTopic = segments.length > 0 ? `${prev.topic}, ${value}` : value;
      return { ...prev, topic: nextTopic };
    });
  };

  const resetExperience = () => {
    setFormData(DEFAULT_FORM);
    setSelectedCategory('');
    setStage('form');
    setTaskId(null);
    setTaskStatus(null);
    setResult(null);
    setError(null);
    setIsLoading(false);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);

    if (!formData.topic.trim()) {
      setError('Please choose or enter a topic before generating a plan.');
      return;
    }

    if (formData.topic.trim() === 'mock_path') {
      setResult(MOCK_PATH);
      setStage('result');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setStage('processing');

    try {
      const goals = formData.goals
        .split(',')
        .map((entry) => entry.trim())
        .filter(Boolean);

      const payload = {
        topic: formData.topic.trim(),
        expertise_level: formData.expertise_level,
        duration_weeks: Number(formData.duration_weeks),
        time_commitment: formData.time_commitment,
        ...(goals.length > 0 ? { goals } : {})
      };

      const response = await generateLearningPath(payload);
      setTaskId(response.task_id);
      setTaskStatus(response.status);
    } catch (submissionError) {
      console.error('Error generating learning path:', submissionError);
      setError(
        submissionError.response?.data?.error ||
          'Failed to start generation. Please try again.'
      );
      setStage('error');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-10 px-4">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6 flex items-center justify-between">
          <div className="inline-flex items-center justify-center gap-3 bg-white/15 border border-white/30 rounded-full px-5 py-2 text-white/90">
            <Wand2 className="w-5 h-5" />
            <span>Personalized learning in minutes</span>
          </div>
          <div className="flex gap-2">
            <a
              href={`${API_BASE_URL}/login/google`}
              className="px-3 py-2 text-white bg-white/10 border border-white/20 rounded-md hover:bg-white/20"
            >
              Sign in with Google
            </a>
            <a href={`${API_BASE_URL}/dashboard`} className="px-3 py-2 text-white bg-white/10 border border-white/20 rounded-md hover:bg-white/20">
              Dashboard
            </a>
          </div>
        </header>

        <div className="text-center mb-10">
          <h1 className="mt-6 text-5xl md:text-6xl font-bold text-white drop-shadow-sm">
            Build a Learning Path You&apos;ll Stick With
          </h1>
          <p className="mt-4 text-lg md:text-xl text-white/75 max-w-2xl mx-auto">
            Mix and match curated AI insights, trusted resources, and your own goals—
            wrapped in the refreshed interface you just shipped.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Button
              onClick={() => {
                const section = document.getElementById('legacy-form-section');
                section?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="bg-white text-[#ff50c5] hover:bg-white/90 font-semibold px-6 py-3 rounded-full"
            >
              Start Planning
            </Button>
            <Button
              variant="outline"
              className="border-white text-white hover:bg-white/10"
              onClick={() => resetExperience()}
            >
              Reset Form
            </Button>
          </div>
        </div>

        {stage === 'form' && (
          <section id="legacy-form-section" className="mb-16">
            <Card className="glass-card border-white/30">
              <CardHeader>
                <CardTitle className="text-3xl font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-7 h-7" />
                  Create Your Learning Path
                </CardTitle>
                <CardDescription className="text-white/75 text-base">
                  Choose a focus area, set your time commitment, and we&apos;ll do the heavy lifting.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-[220px_1fr] gap-6">
                    <div className="space-y-3">
                      <Label className="text-white font-medium">Pick a category</Label>
                      <Select
                        value={selectedCategory}
                        onValueChange={(value) => setSelectedCategory(value)}
                      >
                        <SelectTrigger className="bg-white/10 border-white/20 text-white">
                          <SelectValue placeholder="Select a category" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="programming">Programming &amp; Development</SelectItem>
                          <SelectItem value="data">Data Science &amp; Analytics</SelectItem>
                          <SelectItem value="design">Design &amp; Creativity</SelectItem>
                          <SelectItem value="business">Business &amp; Strategy</SelectItem>
                          <SelectItem value="ai_skills_roles">AI Skills &amp; Roles</SelectItem>
                          <SelectItem value="other">Other Interests</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-3">
                      <Label className="text-white font-medium flex items-center gap-2">
                        <LayoutGrid className="w-4 h-4" />
                        Popular topics
                      </Label>
                      <div className="flex flex-wrap gap-2">
                        {topicSuggestions.length === 0 && (
                          <span className="text-white/60 text-sm">
                            Select a category to see curated suggestions.
                          </span>
                        )}
                        {topicSuggestions.map((item) => (
                          <button
                            type="button"
                            key={item}
                            onClick={() => appendTopic(item)}
                            className="px-3 py-1.5 rounded-full bg-white/15 border border-white/25 text-white/90 text-sm hover:bg-white/25 transition"
                          >
                            {item}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="topic" className="text-white font-medium flex items-center gap-2">
                      <Target className="w-4 h-4" />
                      What do you want to learn?
                    </Label>
                    <Input
                      id="topic"
                      placeholder="e.g., Deep Learning for Computer Vision, Full-stack Web Apps"
                      value={formData.topic}
                      onChange={(event) => handleFormChange('topic', event.target.value)}
                      className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                      required
                    />
                    <p className="text-xs text-white/60">
                      Tip: click suggestions above to auto-fill this field. Use commas to combine multiple focus areas.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-white font-medium flex items-center gap-2">
                        <TrendingUp className="w-4 h-4" />
                        Current expertise level
                      </Label>
                      <Select
                        value={formData.expertise_level}
                        onValueChange={(value) => handleFormChange('expertise_level', value)}
                      >
                        <SelectTrigger className="bg-white/10 border-white/20 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="beginner">Beginner — just starting out</SelectItem>
                          <SelectItem value="intermediate">Intermediate — building confidence</SelectItem>
                          <SelectItem value="advanced">Advanced — aiming for mastery</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-white font-medium flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        Weekly time commitment
                      </Label>
                      <Select
                        value={formData.time_commitment}
                        onValueChange={(value) => handleFormChange('time_commitment', value)}
                      >
                        <SelectTrigger className="bg-white/10 border-white/20 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="minimal">Minimal — 3-5 hours/week</SelectItem>
                          <SelectItem value="moderate">Moderate — 6-10 hours/week</SelectItem>
                          <SelectItem value="intensive">Intensive — 11+ hours/week</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-white font-medium">Duration (weeks)</Label>
                      <Input
                        type="number"
                        min={1}
                        max={52}
                        value={formData.duration_weeks}
                        onChange={(event) => handleFormChange('duration_weeks', Number(event.target.value))}
                        className="bg-white/10 border-white/20 text-white"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-white font-medium">Specific goals (optional)</Label>
                      <Input
                        placeholder="Build a portfolio, earn certification, switch roles"
                        value={formData.goals}
                        onChange={(event) => handleFormChange('goals', event.target.value)}
                        className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                      />
                      <p className="text-xs text-white/60">Separate multiple goals with commas.</p>
                    </div>
                  </div>

                  {error && (
                    <div className="rounded-lg border border-red-300/70 bg-red-500/20 text-white px-4 py-3">
                      {error}
                    </div>
                  )}

                  <Button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-white text-[#ff50c5] hover:bg-white/90 font-semibold text-lg h-12 flex items-center justify-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[#ff50c5]" />
                        Generating your path...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5" />
                        Generate personalized path
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </section>
        )}

        {stage === 'processing' && (
          <section className="max-w-3xl mx-auto">
            <ProgressTracker status={taskStatus} error={null} />
            <div className="mt-6 text-center text-white/75 text-sm">
              We&apos;re enriching resources, filtering noise, and aligning milestones with your goals.
            </div>
          </section>
        )}

        {stage === 'result' && result && (
          <section className="mt-10">
            <LearningPathResult data={result} onReset={resetExperience} />
          </section>
        )}

        {stage === 'error' && (
          <section className="max-w-3xl mx-auto">
            <Card className="glass-card border-white/30 text-center">
              <CardHeader>
                <CardTitle className="text-white text-2xl">Something needs attention</CardTitle>
                <CardDescription className="text-white/75">
                  {error || 'An unexpected error occurred. Please adjust your inputs and try again.'}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button
                  onClick={() => setStage('form')}
                  className="bg-white text-[#ff50c5] hover:bg-white/90 font-semibold"
                >
                  Back to form
                </Button>
                <Button variant="outline" className="border-white text-white hover:bg-white/10" onClick={resetExperience}>
                  Reset everything
                </Button>
              </CardContent>
            </Card>
          </section>
        )}

        <section className="mt-20 grid gap-6 md:grid-cols-3">
          <Card className="glass-card border-white/25">
            <CardHeader>
              <CardTitle className="text-white text-xl flex items-center gap-2">
                <GraduationCap className="w-5 h-5" />
                AI-coached curriculum
              </CardTitle>
            </CardHeader>
            <CardContent className="text-white/75 text-sm">
              Generate clear weekly milestones tuned to your skill level, time budget, and ambitions.
            </CardContent>
          </Card>
          <Card className="glass-card border-white/25">
            <CardHeader>
              <CardTitle className="text-white text-xl flex items-center gap-2">
                <BookOpen className="w-5 h-5" />
                Curated resources only
              </CardTitle>
            </CardHeader>
            <CardContent className="text-white/75 text-sm">
              We vet articles, courses, and projects—automatically dropping broken or gated links.
            </CardContent>
          </Card>
          <Card className="glass-card border-white/25">
            <CardHeader>
              <CardTitle className="text-white text-xl flex items-center gap-2">
                <Rocket className="w-5 h-5" />
                Career aligned insights
              </CardTitle>
            </CardHeader>
            <CardContent className="text-white/75 text-sm">
              Compare market demand, salary ranges, and role expectations without leaving the page.
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}

export default LegacyExperience;
