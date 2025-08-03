import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Workflow {
  workflow_id: string;
  type: string;
  status: string;
  progress: number;
  started_at: string;
  result?: any;
  error?: string;
}

interface WorkflowState {
  activeWorkflows: Record<string, Workflow>;
  completedWorkflows: Workflow[];
}

const initialState: WorkflowState = {
  activeWorkflows: {},
  completedWorkflows: [],
};

const workflowSlice = createSlice({
  name: 'workflow',
  initialState,
  reducers: {
    addWorkflow: (state, action: PayloadAction<Workflow>) => {
      state.activeWorkflows[action.payload.workflow_id] = action.payload;
    },
    updateWorkflow: (state, action: PayloadAction<Partial<Workflow> & { workflow_id: string }>) => {
      const { workflow_id, ...updates } = action.payload;
      if (state.activeWorkflows[workflow_id]) {
        state.activeWorkflows[workflow_id] = {
          ...state.activeWorkflows[workflow_id],
          ...updates,
        };
      }
    },
    completeWorkflow: (state, action: PayloadAction<string>) => {
      const workflow = state.activeWorkflows[action.payload];
      if (workflow) {
        state.completedWorkflows.push({
          ...workflow,
          status: 'completed',
          progress: 100,
        });
        delete state.activeWorkflows[action.payload];
      }
    },
    removeWorkflow: (state, action: PayloadAction<string>) => {
      delete state.activeWorkflows[action.payload];
    },
    clearCompleted: (state) => {
      state.completedWorkflows = [];
    },
  },
});

export const {
  addWorkflow,
  updateWorkflow,
  completeWorkflow,
  removeWorkflow,
  clearCompleted,
} = workflowSlice.actions;

export default workflowSlice.reducer;