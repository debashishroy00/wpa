/**
 * WealthPath AI - Navigation Flow Store (Zustand)
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

// 5-Step Flow Definition based on wireframes
export enum FlowStep {
  DATA_AGGREGATION = 1,
  CURRENT_STATE = 2,
  GOAL_DEFINITION = 3,
  INTELLIGENCE_OUTPUT = 4,
  ACTIONABLE_ROADMAP = 5,
}

export interface StepStatus {
  isCompleted: boolean;
  isActive: boolean;
  canAccess: boolean;
  completedAt?: string;
  data?: Record<string, any>; // Step-specific data
}

export interface FlowState {
  currentStep: FlowStep;
  steps: Record<FlowStep, StepStatus>;
  isFlowStarted: boolean;
  isFlowCompleted: boolean;
  startedAt?: string;
  completedAt?: string;
}

interface NavigationStore extends FlowState {
  // Navigation actions
  goToStep: (step: FlowStep) => void;
  nextStep: () => void;
  previousStep: () => void;
  completeStep: (step: FlowStep, data?: Record<string, any>) => void;
  startFlow: () => void;
  completeFlow: () => void;
  resetFlow: () => void;
  
  // Step data management
  setStepData: (step: FlowStep, data: Record<string, any>) => void;
  getStepData: (step: FlowStep) => Record<string, any> | undefined;
  
  // Computed getters
  getProgress: () => number;
  getCompletedStepsCount: () => number;
  canGoNext: () => boolean;
  canGoPrevious: () => boolean;
  getNextStep: () => FlowStep | null;
  getPreviousStep: () => FlowStep | null;
}

const initialSteps: Record<FlowStep, StepStatus> = {
  [FlowStep.DATA_AGGREGATION]: {
    isCompleted: false,
    isActive: true,
    canAccess: true,
  },
  [FlowStep.CURRENT_STATE]: {
    isCompleted: false,
    isActive: false,
    canAccess: false,
  },
  [FlowStep.GOAL_DEFINITION]: {
    isCompleted: false,
    isActive: false,
    canAccess: false,
  },
  [FlowStep.INTELLIGENCE_OUTPUT]: {
    isCompleted: false,
    isActive: false,
    canAccess: false,
  },
  [FlowStep.ACTIONABLE_ROADMAP]: {
    isCompleted: false,
    isActive: false,
    canAccess: false,
  },
};

export const useNavigationStore = create<NavigationStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        currentStep: FlowStep.DATA_AGGREGATION,
        steps: initialSteps,
        isFlowStarted: false,
        isFlowCompleted: false,
        startedAt: undefined,
        completedAt: undefined,

        // Navigation actions
        goToStep: (step) => {
          const state = get();
          if (state.steps[step].canAccess) {
            set(
              (prev) => ({
                steps: {
                  ...prev.steps,
                  [prev.currentStep]: {
                    ...prev.steps[prev.currentStep],
                    isActive: false,
                  },
                  [step]: {
                    ...prev.steps[step],
                    isActive: true,
                  },
                },
                currentStep: step,
              }),
              false,
              'goToStep'
            );
          }
        },

        nextStep: () => {
          const state = get();
          const nextStep = state.getNextStep();
          if (nextStep && state.canGoNext()) {
            state.goToStep(nextStep);
          }
        },

        previousStep: () => {
          const state = get();
          const previousStep = state.getPreviousStep();
          if (previousStep && state.canGoPrevious()) {
            state.goToStep(previousStep);
          }
        },

        completeStep: (step, data) => {
          set(
            (prev) => {
              const updatedSteps = {
                ...prev.steps,
                [step]: {
                  ...prev.steps[step],
                  isCompleted: true,
                  completedAt: new Date().toISOString(),
                  data: data ? { ...prev.steps[step].data, ...data } : prev.steps[step].data,
                },
              };

              // Enable access to next step
              const nextStepNumber = step + 1;
              if (nextStepNumber <= 5) {
                const nextStep = nextStepNumber as FlowStep;
                updatedSteps[nextStep] = {
                  ...updatedSteps[nextStep],
                  canAccess: true,
                };
              }

              return {
                steps: updatedSteps,
              };
            },
            false,
            'completeStep'
          );
        },

        startFlow: () => {
          set({
            isFlowStarted: true,
            startedAt: new Date().toISOString(),
            currentStep: FlowStep.DATA_AGGREGATION,
            steps: {
              ...initialSteps,
              [FlowStep.DATA_AGGREGATION]: {
                ...initialSteps[FlowStep.DATA_AGGREGATION],
                isActive: true,
              },
            },
          }, false, 'startFlow');
        },

        completeFlow: () => {
          set({
            isFlowCompleted: true,
            completedAt: new Date().toISOString(),
          }, false, 'completeFlow');
        },

        resetFlow: () => {
          set({
            currentStep: FlowStep.DATA_AGGREGATION,
            steps: initialSteps,
            isFlowStarted: false,
            isFlowCompleted: false,
            startedAt: undefined,
            completedAt: undefined,
          }, false, 'resetFlow');
        },

        // Step data management
        setStepData: (step, data) => {
          set(
            (prev) => ({
              steps: {
                ...prev.steps,
                [step]: {
                  ...prev.steps[step],
                  data: { ...prev.steps[step].data, ...data },
                },
              },
            }),
            false,
            'setStepData'
          );
        },

        getStepData: (step) => {
          const state = get();
          return state.steps[step].data;
        },

        // Computed getters
        getProgress: () => {
          const state = get();
          const completedCount = state.getCompletedStepsCount();
          return (completedCount / 5) * 100;
        },

        getCompletedStepsCount: () => {
          const state = get();
          return Object.values(state.steps).filter(step => step.isCompleted).length;
        },

        canGoNext: () => {
          const state = get();
          const currentStepStatus = state.steps[state.currentStep];
          return currentStepStatus.isCompleted && state.currentStep < 5;
        },

        canGoPrevious: () => {
          const state = get();
          return state.currentStep > 1;
        },

        getNextStep: () => {
          const state = get();
          const nextStepNumber = state.currentStep + 1;
          return nextStepNumber <= 5 ? (nextStepNumber as FlowStep) : null;
        },

        getPreviousStep: () => {
          const state = get();
          const previousStepNumber = state.currentStep - 1;
          return previousStepNumber >= 1 ? (previousStepNumber as FlowStep) : null;
        },
      }),
      {
        name: 'wealthpath-navigation-store',
        partialize: (state) => ({
          // Persist flow progress
          currentStep: state.currentStep,
          steps: state.steps,
          isFlowStarted: state.isFlowStarted,
          isFlowCompleted: state.isFlowCompleted,
          startedAt: state.startedAt,
          completedAt: state.completedAt,
        }),
      }
    ),
    {
      name: 'navigation-store',
    }
  )
);

// Step configuration for UI display
export const stepConfig = {
  [FlowStep.DATA_AGGREGATION]: {
    title: 'Data Aggregation',
    description: 'Connect your financial accounts and gather data',
    route: '/dashboard/data-aggregation',
    icon: 'database',
  },
  [FlowStep.CURRENT_STATE]: {
    title: 'Current State Analysis',
    description: 'Analyze your current financial position',
    route: '/dashboard/current-state',
    icon: 'chart-bar',
  },
  [FlowStep.GOAL_DEFINITION]: {
    title: 'Goal Definition',
    description: 'Define your financial goals and targets',
    route: '/dashboard/goals',
    icon: 'target',
  },
  [FlowStep.INTELLIGENCE_OUTPUT]: {
    title: 'AI Intelligence',
    description: 'Get personalized recommendations and insights',
    route: '/dashboard/intelligence',
    icon: 'brain',
  },
  [FlowStep.ACTIONABLE_ROADMAP]: {
    title: 'Action Plan',
    description: 'Receive your personalized financial roadmap',
    route: '/dashboard/roadmap',
    icon: 'map',
  },
};

// Selector hooks
export const useCurrentStep = () => useNavigationStore((state) => state.currentStep);
export const useStepStatus = (step: FlowStep) => useNavigationStore((state) => state.steps[step]);
export const useFlowProgress = () => useNavigationStore((state) => state.getProgress());
export const useIsFlowCompleted = () => useNavigationStore((state) => state.isFlowCompleted);