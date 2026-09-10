export const WARRANTY_TYPES = [
  'Comprehensive Warranty',
  'Manufacturer Warranty',
  'Extended Warranty',
  'Panel Warranty',
  'Compressor Warranty',
  'Motor Warranty',
  'Battery Warranty',
  'Accidental Damage',
  'Screen Protection',
  'Seller Warranty',
  'Other'
];

export const DURATION_PRESETS = [
  { label: '6 Months', value: '6 Months' },
  { label: '1 Year', value: '1 Year' },
  { label: '2 Years', value: '2 Years' },
  { label: '3 Years', value: '3 Years' },
  { label: '5 Years', value: '5 Years' },
  { label: '10 Years', value: '10 Years' },
  { label: 'Custom', value: 'Custom' }
];

export const WARRANTY_STATUS_CONFIG = {
  Active: {
    label: 'Active',
    badgeVariant: 'active',
    iconColor: '#10b981',
    emoji: '🟢'
  },
  'Expiring Soon': {
    label: 'Expiring Soon',
    badgeVariant: 'warning',
    iconColor: '#f59e0b',
    emoji: '🟠'
  },
  Expired: {
    label: 'Expired',
    badgeVariant: 'danger',
    iconColor: '#ef4444',
    emoji: '🔴'
  }
};
