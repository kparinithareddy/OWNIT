export const RETURN_DURATION_PRESETS = [
  { label: '7 Days Replacement', value: '7 Days' },
  { label: '10 Days Replacement', value: '10 Days' },
  { label: '14 Days Return', value: '14 Days' },
  { label: '15 Days Return / Exchange', value: '15 Days' },
  { label: '30 Days Return', value: '30 Days' },
  { label: 'No Returns / Final Sale', value: 'No Returns' },
  { label: 'Custom Duration', value: 'Custom' }
];

export const VERIFIED_SELLER_DEFAULTS = {
  'Amazon India': {
    duration: '7 Days',
    source: 'Amazon India Standard Replacement Policy'
  },
  'Flipkart': {
    duration: '7 Days',
    source: 'Flipkart 7-Day Replacement Policy'
  },
  'Apple Store': {
    duration: '14 Days',
    source: 'Apple Store 14-Day Return Policy'
  },
  'Croma': {
    duration: '15 Days',
    source: 'Croma 15-Day Exchange/Return Policy'
  },
  'Reliance Digital': {
    duration: '7 Days',
    source: 'Reliance Digital 7-Day Replacement Policy'
  },
  'Samsung Shop': {
    duration: '14 Days',
    source: 'Samsung Official Shop 14-Day Return Policy'
  }
};

export const RETURN_STATUS_CONFIG = {
  Active: {
    label: 'Active Return Window',
    badgeVariant: 'active',
    iconColor: '#10b981',
    emoji: '🟢'
  },
  'Ending Soon': {
    label: 'Return Ending Soon',
    badgeVariant: 'warning',
    iconColor: '#f59e0b',
    emoji: '🟠'
  },
  Expired: {
    label: 'Return Window Closed',
    badgeVariant: 'neutral',
    iconColor: '#94a3b8',
    emoji: '🔴'
  },
  Unknown: {
    label: 'No Return Policy Recorded',
    badgeVariant: 'neutral',
    iconColor: '#94a3b8',
    emoji: '⚪'
  }
};
