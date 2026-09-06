import { useState } from 'react';
import { Sparkles, Clock, Target, TrendingUp } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

export default function LearningPathForm({ onSubmit, isLoading }) {
  const [formData, setFormData] = useState({
    topic: '',
    expertise_level: 'beginner',
    duration_weeks: 4,
    time_commitment: 'moderate',
    goals: '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Convert goals string to array
    const goals = formData.goals
      .split(',')
      .map(g => g.trim())
      .filter(g => g.length > 0);
    
    onSubmit({
      ...formData,
      goals: goals.length > 0 ? goals : undefined,
    });
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Card className="glass-card border-white/20">
      <CardHeader>
        <CardTitle className="text-3xl font-bold text-white flex items-center gap-2">
          <Sparkles className="w-8 h-8" />
          Create Your Learning Path
        </CardTitle>
        <CardDescription className="text-white/80 text-base">
          AI-powered personalized learning paths with real-time job market insights
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Topic */}
          <div className="space-y-2">
            <Label htmlFor="topic" className="text-white font-medium flex items-center gap-2">
              <Target className="w-4 h-4" />
              What do you want to learn?
            </Label>
            <Input
              id="topic"
              placeholder="e.g., Python Data Analysis, Machine Learning, Web Development"
              value={formData.topic}
              onChange={(e) => handleChange('topic', e.target.value)}
              required
              className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
            />
          </div>

          {/* Expertise Level */}
          <div className="space-y-2">
            <Label htmlFor="expertise" className="text-white font-medium flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Current Expertise Level
            </Label>
            <Select value={formData.expertise_level} onValueChange={(value) => handleChange('expertise_level', value)}>
              <SelectTrigger className="bg-white/10 border-white/20 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="beginner">Beginner - Just starting out</SelectItem>
                <SelectItem value="intermediate">Intermediate - Some experience</SelectItem>
                <SelectItem value="advanced">Advanced - Looking to specialize</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Duration and Time Commitment */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="duration" className="text-white font-medium flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Duration (weeks)
              </Label>
              <Input
                id="duration"
                type="number"
                min="1"
                max="52"
                value={formData.duration_weeks}
                onChange={(e) => handleChange('duration_weeks', parseInt(e.target.value))}
                required
                className="bg-white/10 border-white/20 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="commitment" className="text-white font-medium">
                Time Commitment
              </Label>
              <Select value={formData.time_commitment} onValueChange={(value) => handleChange('time_commitment', value)}>
                <SelectTrigger className="bg-white/10 border-white/20 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="minimal">Minimal - Few hours/week</SelectItem>
                  <SelectItem value="moderate">Moderate - 5-10 hours/week</SelectItem>
                  <SelectItem value="intensive">Intensive - 15+ hours/week</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Goals (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="goals" className="text-white font-medium">
              Specific Goals (Optional)
            </Label>
            <Input
              id="goals"
              placeholder="e.g., Build portfolio projects, Get certified, Switch careers"
              value={formData.goals}
              onChange={(e) => handleChange('goals', e.target.value)}
              className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
            />
            <p className="text-xs text-white/60">Separate multiple goals with commas</p>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-white text-purple-600 hover:bg-white/90 font-semibold text-lg h-12"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600 mr-2" />
                Generating Your Path...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 mr-2" />
                Generate Learning Path
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
