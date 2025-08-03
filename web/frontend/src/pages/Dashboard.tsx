import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="overline">
            {title}
          </Typography>
          <Typography variant="h4">{value}</Typography>
        </Box>
        <Box sx={{ color }}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

interface WorkflowItemProps {
  workflow: any;
}

const WorkflowItem: React.FC<WorkflowItemProps> = ({ workflow }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'primary';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography variant="h6">{workflow.type}</Typography>
          <Typography variant="body2" color="textSecondary">
            Started: {new Date(workflow.started_at).toLocaleString()}
          </Typography>
        </Box>
        <Box display="flex" alignItems="center" gap={2}>
          <Chip 
            label={workflow.status} 
            color={getStatusColor(workflow.status) as any}
            size="small"
          />
          {workflow.status === 'running' && (
            <Box sx={{ width: 100 }}>
              <LinearProgress 
                variant="determinate" 
                value={workflow.progress} 
              />
            </Box>
          )}
        </Box>
      </Box>
    </Paper>
  );
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  
  // Fetch career database status
  const { data: dbData } = useQuery({
    queryKey: ['career-database'],
    queryFn: api.getCareerDatabase,
    retry: false,
  });

  // Fetch recent workflows
  const { data: workflowsData } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.listWorkflows,
  });

  const stats = {
    totalExperiences: dbData?.database?.experiences?.length || 0,
    analyzedJobs: workflowsData?.workflows?.filter((w: any) => w.type === 'job_analysis').length || 0,
    generatedDocs: workflowsData?.workflows?.filter((w: any) => 
      w.type === 'cv_generation' || w.type === 'cover_letter_generation'
    ).length || 0,
    activeWorkflows: workflowsData?.workflows?.filter((w: any) => w.status === 'running').length || 0,
  };

  const recentWorkflows = workflowsData?.workflows?.slice(0, 5) || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Career Experiences"
            value={stats.totalExperiences}
            icon={<TrendingUpIcon fontSize="large" />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Jobs Analyzed"
            value={stats.analyzedJobs}
            icon={<AssignmentIcon fontSize="large" />}
            color="#388e3c"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Documents Generated"
            value={stats.generatedDocs}
            icon={<CheckCircleIcon fontSize="large" />}
            color="#f57c00"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Workflows"
            value={stats.activeWorkflows}
            icon={<ScheduleIcon fontSize="large" />}
            color="#d32f2f"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            {recentWorkflows.length === 0 ? (
              <Typography color="textSecondary">
                No recent workflows. Start by building your career database!
              </Typography>
            ) : (
              recentWorkflows.map((workflow: any) => (
                <WorkflowItem key={workflow.workflow_id} workflow={workflow} />
              ))
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              {!dbData && (
                <Button
                  variant="contained"
                  color="primary"
                  fullWidth
                  onClick={() => navigate('/career-database')}
                >
                  Build Career Database
                </Button>
              )}
              <Button
                variant="outlined"
                fullWidth
                onClick={() => navigate('/job-analysis')}
                disabled={!dbData}
              >
                Analyze New Job
              </Button>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => navigate('/documents')}
                disabled={!dbData}
              >
                Generate Documents
              </Button>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => navigate('/workflows')}
              >
                View All Workflows
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;