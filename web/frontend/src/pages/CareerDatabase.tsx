import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Grid,
  Card,
  CardContent,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CloudUpload as CloudUploadIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import ReactMarkdown from 'react-markdown';
import YAML from 'yaml';

const CareerDatabase: React.FC = () => {
  const [documentsPath, setDocumentsPath] = useState('');
  const [buildWorkflowId, setBuildWorkflowId] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedExperience, setSelectedExperience] = useState<any>(null);
  const queryClient = useQueryClient();

  // Fetch career database
  const { data: dbData, isLoading, error, refetch } = useQuery({
    queryKey: ['career-database'],
    queryFn: api.getCareerDatabase,
    retry: false,
  });

  // WebSocket for workflow updates
  const { status: wsStatus, progress: wsProgress } = useWebSocket(buildWorkflowId);

  // Build database mutation
  const buildMutation = useMutation({
    mutationFn: api.buildCareerDatabase,
    onSuccess: (data) => {
      setBuildWorkflowId(data.workflow_id);
    },
  });

  // File upload
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // In a real implementation, you would upload files and get a directory path
    // For now, we'll just show a message
    console.log('Files to upload:', acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
    },
    multiple: true,
  });

  const handleBuildDatabase = () => {
    if (!documentsPath) {
      alert('Please enter a documents directory path');
      return;
    }
    buildMutation.mutate({ documents_directory: documentsPath });
  };

  const handleEditExperience = (experience: any) => {
    setSelectedExperience(experience);
    setEditDialogOpen(true);
  };

  const renderExperience = (exp: any, index: number) => (
    <Accordion key={index}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
          <Typography variant="h6">{exp.title || exp.role || 'Untitled'}</Typography>
          <Typography color="textSecondary">
            {exp.company || exp.organization || 'Unknown Company'}
          </Typography>
          {exp.period && (
            <Chip 
              label={exp.period} 
              size="small" 
              variant="outlined"
              sx={{ ml: 'auto', mr: 2 }}
            />
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Box display="flex" justifyContent="flex-end" gap={1} mb={2}>
              <IconButton size="small" onClick={() => handleEditExperience(exp)}>
                <EditIcon />
              </IconButton>
              <IconButton size="small" color="error">
                <DeleteIcon />
              </IconButton>
            </Box>
          </Grid>
          
          {exp.description && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>Description</Typography>
              <Typography variant="body2" paragraph>
                <ReactMarkdown>{exp.description}</ReactMarkdown>
              </Typography>
            </Grid>
          )}
          
          {exp.achievements && exp.achievements.length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>Achievements</Typography>
              <ul>
                {exp.achievements.map((achievement: string, i: number) => (
                  <li key={i}>
                    <Typography variant="body2">{achievement}</Typography>
                  </li>
                ))}
              </ul>
            </Grid>
          )}
          
          {exp.technologies && exp.technologies.length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>Technologies</Typography>
              <Box display="flex" gap={1} flexWrap="wrap">
                {exp.technologies.map((tech: string, i: number) => (
                  <Chip key={i} label={tech} size="small" />
                ))}
              </Box>
            </Grid>
          )}
        </Grid>
      </AccordionDetails>
    </Accordion>
  );

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Typography variant="h4">Career Database</Typography>
        {dbData && (
          <Button
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            variant="outlined"
          >
            Refresh
          </Button>
        )}
      </Box>

      {!dbData && !error ? (
        <Paper sx={{ p: 4 }}>
          <Typography variant="h6" gutterBottom>
            Build Your Career Database
          </Typography>
          <Typography variant="body1" paragraph>
            To get started, we need to scan your career documents (resume, CV, etc.) 
            and build a comprehensive database of your experiences.
          </Typography>

          <Box sx={{ my: 3 }}>
            <TextField
              fullWidth
              label="Documents Directory Path"
              value={documentsPath}
              onChange={(e) => setDocumentsPath(e.target.value)}
              placeholder="/path/to/your/documents"
              helperText="Enter the full path to the directory containing your career documents"
            />
          </Box>

          <Typography variant="body2" paragraph>
            Or drag and drop your documents here:
          </Typography>

          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed #ccc',
              borderRadius: 2,
              p: 3,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'action.hover' : 'background.paper',
              mb: 3,
            }}
          >
            <input {...getInputProps()} />
            <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography>
              {isDragActive
                ? 'Drop the files here...'
                : 'Drag and drop files here, or click to select'}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Supported: PDF, Word, TXT, Markdown
            </Typography>
          </Box>

          <Button
            variant="contained"
            size="large"
            onClick={handleBuildDatabase}
            disabled={buildMutation.isPending || !documentsPath}
            fullWidth
          >
            {buildMutation.isPending ? 'Building...' : 'Build Career Database'}
          </Button>

          {buildWorkflowId && wsStatus === 'running' && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="body2" gutterBottom>
                Building database... {wsProgress}%
              </Typography>
              <CircularProgress variant="determinate" value={wsProgress} />
            </Box>
          )}

          {buildMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              Failed to build database. Please check the path and try again.
            </Alert>
          )}
        </Paper>
      ) : dbData ? (
        <Box>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Work Experiences ({dbData.database.experiences?.length || 0})
                </Typography>
                {dbData.database.experiences?.map((exp: any, index: number) => 
                  renderExperience(exp, index)
                )}
              </Paper>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Database Summary
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Last Updated: {new Date(dbData.last_modified).toLocaleDateString()}
                  </Typography>
                  <Typography variant="body2">
                    Total Experiences: {dbData.database.experiences?.length || 0}
                  </Typography>
                  <Typography variant="body2">
                    Skills: {dbData.database.skills?.length || 0}
                  </Typography>
                  <Typography variant="body2">
                    Education: {dbData.database.education?.length || 0}
                  </Typography>
                </CardContent>
              </Card>

              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Actions
                  </Typography>
                  <Box display="flex" flexDirection="column" gap={2}>
                    <Button variant="outlined" fullWidth>
                      Export as YAML
                    </Button>
                    <Button variant="outlined" fullWidth>
                      Export as JSON
                    </Button>
                    <Button 
                      variant="outlined" 
                      color="warning"
                      fullWidth
                      onClick={() => setBuildWorkflowId(null)}
                    >
                      Rebuild Database
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      ) : (
        <Alert severity="error">
          Failed to load career database. {error?.message}
        </Alert>
      )}

      {/* Edit Dialog */}
      <Dialog 
        open={editDialogOpen} 
        onClose={() => setEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Edit Experience</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={10}
            value={selectedExperience ? YAML.stringify(selectedExperience) : ''}
            sx={{ mt: 2, fontFamily: 'monospace' }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => setEditDialogOpen(false)}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CareerDatabase;