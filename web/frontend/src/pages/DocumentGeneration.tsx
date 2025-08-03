import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  ToggleButton,
  ToggleButtonGroup,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Alert,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  Email as EmailIcon,
  Download as DownloadIcon,
  Preview as PreviewIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import ReactMarkdown from 'react-markdown';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`document-tabpanel-${index}`}
      aria-labelledby={`document-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const DocumentGeneration: React.FC = () => {
  const [documentType, setDocumentType] = useState<'cv' | 'cover_letter'>('cv');
  const [tabValue, setTabValue] = useState(0);
  const [jobUrl, setJobUrl] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [template, setTemplate] = useState('default');
  const [tone, setTone] = useState('professional');
  const [generatedDocument, setGeneratedDocument] = useState('');

  // Generate document mutation
  const generateMutation = useMutation({
    mutationFn: api.generateDocument,
    onSuccess: (data) => {
      // In a real app, you'd poll the workflow and get the document
      setGeneratedDocument('# Generated Document\n\nThis is a preview of your generated document...');
    },
  });

  const handleGenerate = () => {
    if (!jobUrl) {
      alert('Please enter a job URL');
      return;
    }
    
    generateMutation.mutate({
      job_url: jobUrl,
      job_title: jobTitle || undefined,
      company_name: companyName || undefined,
      document_type: documentType,
      template: documentType === 'cv' ? template : undefined,
      tone: documentType === 'cover_letter' ? tone : undefined,
    });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Document Generation
      </Typography>

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Generate New" />
          <Tab label="Templates" />
          <Tab label="History" />
        </Tabs>
      </Paper>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Document Settings
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Document Type
                </Typography>
                <ToggleButtonGroup
                  value={documentType}
                  exclusive
                  onChange={(e, value) => value && setDocumentType(value)}
                  fullWidth
                >
                  <ToggleButton value="cv">
                    <DescriptionIcon sx={{ mr: 1 }} />
                    CV/Resume
                  </ToggleButton>
                  <ToggleButton value="cover_letter">
                    <EmailIcon sx={{ mr: 1 }} />
                    Cover Letter
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>

              <TextField
                fullWidth
                label="Job URL"
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                placeholder="https://example.com/careers/position"
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Job Title (Optional)"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="Senior Software Engineer"
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                label="Company Name (Optional)"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="TechCorp Inc."
                sx={{ mb: 3 }}
              />

              {documentType === 'cv' ? (
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>CV Template</InputLabel>
                  <Select
                    value={template}
                    onChange={(e) => setTemplate(e.target.value)}
                    label="CV Template"
                  >
                    <MenuItem value="default">Default - Clean & Professional</MenuItem>
                    <MenuItem value="technical">Technical - Skills Focused</MenuItem>
                    <MenuItem value="executive">Executive - Leadership Focused</MenuItem>
                    <MenuItem value="creative">Creative - Design Forward</MenuItem>
                  </Select>
                </FormControl>
              ) : (
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Writing Tone</InputLabel>
                  <Select
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    label="Writing Tone"
                  >
                    <MenuItem value="professional">Professional</MenuItem>
                    <MenuItem value="enthusiastic">Enthusiastic</MenuItem>
                    <MenuItem value="conversational">Conversational</MenuItem>
                    <MenuItem value="formal">Formal</MenuItem>
                  </Select>
                </FormControl>
              )}

              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={handleGenerate}
                disabled={generateMutation.isPending}
              >
                Generate {documentType === 'cv' ? 'CV' : 'Cover Letter'}
              </Button>

              {generateMutation.isError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  Failed to generate document. Please try again.
                </Alert>
              )}
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, minHeight: 500 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Document Preview
                </Typography>
                {generatedDocument && (
                  <Box>
                    <Button startIcon={<PreviewIcon />} sx={{ mr: 1 }}>
                      Full Preview
                    </Button>
                    <Button startIcon={<DownloadIcon />} variant="contained">
                      Download
                    </Button>
                  </Box>
                )}
              </Box>
              
              {generatedDocument ? (
                <Box
                  sx={{
                    border: '1px solid #e0e0e0',
                    borderRadius: 1,
                    p: 3,
                    bgcolor: 'background.paper',
                    maxHeight: 600,
                    overflow: 'auto',
                  }}
                >
                  <ReactMarkdown>{generatedDocument}</ReactMarkdown>
                </Box>
              ) : (
                <Box
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  height={400}
                  sx={{
                    border: '2px dashed #e0e0e0',
                    borderRadius: 1,
                    color: 'text.secondary',
                  }}
                >
                  <Typography>
                    Generated document will appear here
                  </Typography>
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          {['Default', 'Technical', 'Executive', 'Creative'].map((templateName) => (
            <Grid item xs={12} sm={6} md={3} key={templateName}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {templateName} Template
                  </Typography>
                  <Typography variant="body2" color="textSecondary" paragraph>
                    {templateName === 'Default' && 'Clean and professional layout suitable for most industries'}
                    {templateName === 'Technical' && 'Emphasizes technical skills and project experience'}
                    {templateName === 'Executive' && 'Highlights leadership and strategic achievements'}
                    {templateName === 'Creative' && 'Modern design with visual appeal'}
                  </Typography>
                  <Button variant="outlined" size="small" fullWidth>
                    Preview
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Typography variant="body1" color="textSecondary">
          Document generation history will appear here
        </Typography>
      </TabPanel>
    </Box>
  );
};

export default DocumentGeneration;