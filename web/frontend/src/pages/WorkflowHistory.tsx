import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as VisibilityIcon,
  Refresh as RefreshIcon,
  FilterList as FilterListIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { formatDistanceToNow } from 'date-fns';

interface WorkflowRow {
  workflow_id: string;
  type: string;
  status: string;
  progress: number;
  started_at: string;
  completed_at?: string;
  error?: string;
}

const WorkflowHistory: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  // Fetch workflows
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.listWorkflows,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const workflows: WorkflowRow[] = data?.workflows || [];

  // Filter workflows
  const filteredWorkflows = workflows.filter((workflow) => {
    const matchesSearch = searchTerm === '' || 
      workflow.workflow_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      workflow.type.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || workflow.status === statusFilter;
    const matchesType = typeFilter === 'all' || workflow.type === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getStatusChip = (status: string) => {
    const statusConfig = {
      completed: { color: 'success' as const, label: 'Completed' },
      running: { color: 'primary' as const, label: 'Running' },
      failed: { color: 'error' as const, label: 'Failed' },
      started: { color: 'default' as const, label: 'Started' },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || {
      color: 'default' as const,
      label: status,
    };

    return <Chip label={config.label} color={config.color} size="small" />;
  };

  const getWorkflowTypeLabel = (type: string) => {
    const typeLabels: Record<string, string> = {
      database_build: 'Database Build',
      job_analysis: 'Job Analysis',
      cv_generation: 'CV Generation',
      cover_letter_generation: 'Cover Letter',
    };
    return typeLabels[type] || type;
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Workflow History
        </Typography>
        <IconButton onClick={() => refetch()} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      <Paper sx={{ mb: 2, p: 2 }}>
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            size="small"
            placeholder="Search workflows..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ flex: 1, maxWidth: 400 }}
          />

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              label="Status"
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="running">Running</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Type</InputLabel>
            <Select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              label="Type"
            >
              <MenuItem value="all">All Types</MenuItem>
              <MenuItem value="database_build">Database Build</MenuItem>
              <MenuItem value="job_analysis">Job Analysis</MenuItem>
              <MenuItem value="cv_generation">CV Generation</MenuItem>
              <MenuItem value="cover_letter_generation">Cover Letter</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        {isLoading && <LinearProgress />}
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Workflow ID</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredWorkflows
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((workflow) => (
                <TableRow key={workflow.workflow_id}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {workflow.workflow_id.substring(0, 8)}...
                    </Typography>
                  </TableCell>
                  <TableCell>{getWorkflowTypeLabel(workflow.type)}</TableCell>
                  <TableCell>{getStatusChip(workflow.status)}</TableCell>
                  <TableCell>
                    {workflow.status === 'running' ? (
                      <Box display="flex" alignItems="center" gap={1}>
                        <LinearProgress
                          variant="determinate"
                          value={workflow.progress}
                          sx={{ width: 100 }}
                        />
                        <Typography variant="body2">{workflow.progress}%</Typography>
                      </Box>
                    ) : (
                      <Typography variant="body2">
                        {workflow.status === 'completed' ? '100%' : '-'}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {formatDistanceToNow(new Date(workflow.started_at), { addSuffix: true })}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton size="small">
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            
            {filteredWorkflows.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2" color="textSecondary">
                    No workflows found
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredWorkflows.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>

      <Box mt={3}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Summary
          </Typography>
          <Box display="flex" gap={4}>
            <Box>
              <Typography variant="body2" color="textSecondary">
                Total Workflows
              </Typography>
              <Typography variant="h5">
                {workflows.length}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="textSecondary">
                Completed
              </Typography>
              <Typography variant="h5" color="success.main">
                {workflows.filter(w => w.status === 'completed').length}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="textSecondary">
                Running
              </Typography>
              <Typography variant="h5" color="primary.main">
                {workflows.filter(w => w.status === 'running').length}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="textSecondary">
                Failed
              </Typography>
              <Typography variant="h5" color="error.main">
                {workflows.filter(w => w.status === 'failed').length}
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};

export default WorkflowHistory;