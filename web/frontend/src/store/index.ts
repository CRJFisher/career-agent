import { configureStore } from '@reduxjs/toolkit';
import workflowReducer from './workflowSlice';
import uiReducer from './uiSlice';

export const store = configureStore({
  reducer: {
    workflow: workflowReducer,
    ui: uiReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;