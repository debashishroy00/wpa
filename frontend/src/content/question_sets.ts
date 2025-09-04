export type QuestionTile = {
  id: string;
  label: string;
  sublabel?: string;
  prompt: string; // precomposed chat message that maps to an existing calc
};

export type QuestionCategory = {
  id: string;
  title: string;
  tiles: QuestionTile[];
};

// v1 static catalog – safe defaults; maps to existing chat/calculator phrasing
export const QUESTION_SETS: QuestionCategory[] = [
  {
    id: 'retirement',
    title: 'Retirement',
    tiles: [
      { id: 'retire_on_track', label: 'Am I on track?', prompt: 'Am I on track for my retirement goal?' },
      { id: 'goal_in_2y', label: 'Goal if retiring in 2 years', prompt: 'What if I retire in 2 years, what should be my goal?' },
      { id: 'monthly_for_target', label: 'Monthly needed for $3.5M in 5 years', prompt: 'How much should I save monthly to reach $3,500,000 in 5 years?' },
      { id: 'withdrawal_check', label: 'Safe withdrawal check (4%)', prompt: 'Can I safely withdraw 4% from my portfolio?' }
    ]
  },
  {
    id: 'investing',
    title: 'Investing',
    tiles: [
      { id: 'rebalance', label: 'Rebalance to target', prompt: 'Should I rebalance my portfolio? What trades are needed to reach target allocation?' },
      { id: 'projection_10y', label: '10-year projection (5/7/9%)', prompt: 'What is my net worth projection in 10 years? Show scenarios at 5%, 7% and 9% growth.' },
      { id: 'asset_location', label: 'Tax-efficient asset location', prompt: 'How should I place assets across accounts for tax efficiency?' },
      { id: 'fees', label: 'Fees & drag audit', prompt: 'Am I paying too much in fees? Quantify fees and performance drag.' }
    ]
  },
  {
    id: 'taxes',
    title: 'Taxes',
    tiles: [
      { id: 'tax_bracket', label: 'Tax bracket & marginal (this year)', prompt: 'What is my tax bracket and marginal rate this year?' },
      { id: 'roth_vs_trad', label: 'Roth vs Traditional (this year)', prompt: 'Should I contribute Roth or Traditional this year?' },
      { id: 'roth_conv', label: 'Roth conversion window', prompt: 'Do I have a Roth conversion window this year?' },
      { id: 'tlh', label: 'Tax-loss harvest candidates', prompt: 'Do I have tax-loss harvesting candidates right now?' }
    ]
  },
  {
    id: 'expenses',
    title: 'Expenses',
    tiles: [
      { id: 'breakdown', label: 'Monthly expense breakdown', prompt: 'Show a breakdown of my expenses for the last full month.' },
      { id: 'overspend_trends', label: 'Overspending & trends (3 months)', prompt: 'Find overspending and trends over the last 3 months.' },
      { id: 'subscriptions', label: 'Hidden subscriptions', prompt: 'List all subscriptions and price changes.' },
      { id: 'peer_compare', label: 'Compare vs peers (state/city)', prompt: 'Compare my spending to peers in my area.' }
    ]
  }
];

