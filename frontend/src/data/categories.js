/**
 * Product Categories supported by OWNIT
 */

export const PRODUCT_CATEGORIES = [
  'Mobile',
  'Laptop',
  'TV',
  'Refrigerator',
  'Washing Machine',
  'Air Conditioner',
  'Audio',
  'Camera',
  'Gaming',
  'Home Appliance',
  'Other'
];

export const CATEGORY_OPTIONS = PRODUCT_CATEGORIES.map((cat) => ({
  value: cat,
  label: cat
}));
