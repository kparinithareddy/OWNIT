/**
 * Document Types supported in OWNIT
 */

export const DOCUMENT_TYPES = [
  'Purchase Bill',
  'Warranty Card',
  'Extended Warranty',
  'User Manual',
  'Service Invoice',
  'Other'
];

export const DOCUMENT_TYPE_OPTIONS = DOCUMENT_TYPES.map((type) => ({
  value: type,
  label: type
}));
