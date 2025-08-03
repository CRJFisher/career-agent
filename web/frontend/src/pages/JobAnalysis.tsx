import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  TrendingUp as TrendingUpIcon,
  Business as BusinessIcon,
  Work as WorkIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';

interface FitScoreProps {
  label: string;
  score: number;
  color: string;
}

const FitScore: React.FC<FitScoreProps> = ({ label, score, color }) => (
  <Box sx={{ mb: 2 }}>
    <Box display="flex" justifyContent="space-between" mb={1}>
      <Typography variant="body2">{label}</Typography>
      <Typography variant="body2" fontWeight="bold">{score}%</Typography>
    </Box>
    <LinearProgress
      variant="determinate"
      value={score}
      sx={{
        height: 8,
        borderRadius: 4,
        backgroundColor: '#e0e0e0',
        '& .MuiLinearProgress-bar': {
          backgroundColor: color,
          borderRadius: 4,
        },
      }}
    />
  </Box>
);

const JobAnalysis: React.FC = () => {
  const [jobUrl, setJobUrl] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [analysisWorkflowId, setAnalysisWorkflowId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  // WebSocket for workflow updates
  const { status: wsStatus, progress: wsProgress, data: wsData } = useWebSocket(analysisWorkflowId);

  // Analyze job mutation
  const analyzeMutation = useMutation({
    mutationFn: api.analyzeJob,
    onSuccess: (data) => {
      setAnalysisWorkflowId(data.workflow_id);
    },
  });

  // Handle WebSocket data updates
  React.useEffect(() => {
    if (wsData?.type === 'completed' && wsData.data?.result) {
      setAnalysisResult(wsData.data.result);
    }
  }, [wsData]);

  const handleAnalyze = () => {
    if (!jobUrl) {
      alert('Please enter a job URL');
      return;
    }
    analyzeMutation.mutate({ 
      job_url: jobUrl, 
      job_description: jobDescription || undefined 
    });
  };

  const renderAnalysisResult = () => {
    if (!analysisResult) return null;

    const overallScore = analysisResult.overall_fit_score || 
      Math.round((analysisResult.technical_fit_score + analysisResult.cultural_fit_score) / 2);

    return (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={3}>
                <BusinessIcon color="primary" />
                <Box>
                  <Typography variant="h5">
                    {analysisResult.job_title || 'Position'}
                  </Typography>
                  <Typography color="textSecondary">
                    {analysisResult.company || 'Company'}
                  </Typography>
                </Box>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <FitScore
                    label="Technical Fit"
                    score={analysisResult.technical_fit_score || 0}
                    color="#1976d2"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <FitScore
                    label="Cultural Fit"
                    score={analysisResult.cultural_fit_score || 0}
                    color="#388e3c"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <FitScore
                    label="Overall Fit"
                    score={overallScore}
                    color="#f57c00"
                  />
                </Grid>
              </Grid>

              <Box mt={3}>
                <Chip
                  label={overallScore >= 80 ? 'Excellent Match' : 
                         overallScore >= 60 ? 'Good Match' : 
                         overallScore >= 40 ? 'Moderate Match' : 'Low Match'}
                  color={overallScore >= 60 ? 'success' : 'warning'}
                  size="medium"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom display="flex" alignItems="center" gap={1}>
              <CheckCircleIcon color="success" />
              Key Strengths
            </Typography>
            <List>
              {analysisResult.key_strengths?.map((strength: string, index: number) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <TrendingUpIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={strength} />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom display="flex" alignItems="center" gap={1}>
              <CancelIcon color="error" />
              Critical Gaps
            </Typography>
            <List>
              {analysisResult.critical_gaps?.map((gap: string, index: number) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <CancelIcon color="error" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={gap} />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {analysisResult.recommendation && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Recommendation
              </Typography>
              <Typography variant="body1" paragraph>
                {analysisResult.recommendation}
              </Typography>
              <Box display="flex" gap={2} mt={3}>
                <Button 
                  variant="contained" 
                  color="primary"
                  startIcon={<WorkIcon />}
                >
                  Generate Tailored CV
                </Button>
                <Button 
                  variant="outlined"
                  startIcon={<WorkIcon />}
                >
                  Generate Cover Letter
                </Button>
              </Box>
            </Paper>
          </Grid>
        )}
      </Grid>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Job Analysis
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Analyze Job Posting
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Job URL"
              value={jobUrl}
              onChange={(e) => setJobUrl(e.target.value)}
              placeholder="https://example.com/careers/software-engineer"
              helperText="Enter the URL of the job posting"
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Job Description (Optional)"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here if the URL doesn't work..."
              helperText="Optional: Provide the job description directly"
            />
          </Grid>
          
          <Grid item xs={12}>
            <Button
              variant="contained"
              size="large"
              onClick={handleAnalyze}
              disabled={analyzeMutation.isPending || wsStatus === 'running'}
              fullWidth
            >
              {analyzeMutation.isPending || wsStatus === 'running' 
                ? `Analyzing... ${wsProgress}%` 
                : 'Analyze Job Fit'}
            </Button>
          </Grid>
        </Grid>

        {analyzeMutation.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to analyze job. Please check the URL and try again.
          </Alert>
        )}

        {wsStatus === 'running' && (
          <Box sx={{ mt: 3 }}>
            <LinearProgress variant="determinate" value={wsProgress} />
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              {wsProgress < 30 ? 'Extracting job requirements...' :
               wsProgress < 60 ? 'Analyzing your fit...' :
               'Generating recommendations...'}
            </Typography>
          </Box>
        )}
      </Paper>

      {analysisResult && renderAnalysisResult()}
    </Box>
  );
};

export default JobAnalysis;