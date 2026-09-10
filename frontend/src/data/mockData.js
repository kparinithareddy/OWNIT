/**
 * OWNIT - Mock Data for Frontend Demonstration
 * Clean placeholder datasets for student project evaluation.
 */

export const mockProducts = [
  {
    id: 'prod-1',
    name: 'Apple MacBook Pro 14"',
    category: 'Electronics',
    brand: 'Apple',
    model: 'M3 Pro / 18GB / 512GB',
    serialNumber: 'C02G8393MD6T',
    purchaseDate: '2024-03-15',
    purchasePrice: '₹1,99,900',
    store: 'Apple Store BKC',
    warrantyExpiry: '2025-03-14',
    warrantyStatus: 'active', // 'active' | 'expiring' | 'expired'
    returnPeriodExpiry: '2024-03-29',
    lifeScore: 94,
    hasReceipt: true,
    hasWarrantyCard: true,
    thumbnailIcon: 'Laptop',
    description: 'Main work laptop. Covers AppleCare+ standard limited warranty.',
    warrantyDetails: {
      provider: 'AppleCare Limited Warranty',
      durationMonths: 12,
      inclusions: ['Hardware defects', 'Battery below 80%', 'Keyboard issues'],
      exclusions: ['Accidental water damage', 'Cosmetic scratches']
    },
    maintenanceHistory: [
      { date: '2024-03-15', title: 'Device Registered', type: 'system' },
      { date: '2024-06-10', title: 'macOS Sequoia Update', type: 'software' }
    ]
  },
  {
    id: 'prod-2',
    name: 'Sony WH-1000XM5 Headphones',
    category: 'Audio',
    brand: 'Sony',
    model: 'WH-1000XM5 Silver',
    serialNumber: 'S01-9482910-B',
    purchaseDate: '2023-10-20',
    purchasePrice: '₹26,990',
    store: 'Amazon India',
    warrantyExpiry: '2024-10-19',
    warrantyStatus: 'expiring',
    returnPeriodExpiry: '2023-10-30',
    lifeScore: 88,
    hasReceipt: true,
    hasWarrantyCard: true,
    thumbnailIcon: 'Headphones',
    description: 'Active Noise Cancelling over-ear wireless headphones.',
    warrantyDetails: {
      provider: 'Sony India 1-Year Standard',
      durationMonths: 12,
      inclusions: ['Driver failure', 'Bluetooth connectivity defects', 'Charging port failure'],
      exclusions: ['Physical headband snapping', 'Earcup tear from wear']
    },
    maintenanceHistory: [
      { date: '2023-10-20', title: 'Purchased on Amazon', type: 'system' },
      { date: '2024-04-12', title: 'Firmware v2.1.0 update', type: 'software' }
    ]
  },
  {
    id: 'prod-3',
    name: 'Samsung 324L Double Door Refrigerator',
    category: 'Home Appliances',
    brand: 'Samsung',
    model: 'RT34T4513S8',
    serialNumber: 'SAM-REF-2022-991',
    purchaseDate: '2022-08-05',
    purchasePrice: '₹34,500',
    store: 'Reliance Digital',
    warrantyExpiry: '2032-08-04',
    warrantyStatus: 'active',
    returnPeriodExpiry: '2022-08-15',
    lifeScore: 92,
    hasReceipt: true,
    hasWarrantyCard: true,
    thumbnailIcon: 'Refrigerator',
    description: 'Digital Inverter frost free double door refrigerator with 10-year compressor warranty.',
    warrantyDetails: {
      provider: 'Samsung 10-Yr Compressor Warranty',
      durationMonths: 120,
      inclusions: ['Digital inverter compressor replacement', 'Gas charging on failure'],
      exclusions: ['Plastic shelves breakage', 'Bulb replacement']
    },
    maintenanceHistory: [
      { date: '2022-08-05', title: 'Installation & Registration', type: 'service' },
      { date: '2023-09-14', title: 'Annual Coil Cleaning', type: 'maintenance' }
    ]
  },
  {
    id: 'prod-4',
    name: 'Dyson V12 Detect Slim Vacuum',
    category: 'Home Appliances',
    brand: 'Dyson',
    model: 'V12 Detect Cordless',
    serialNumber: 'DYS-V12-449102',
    purchaseDate: '2023-01-10',
    purchasePrice: '₹45,900',
    store: 'Dyson Official Store',
    warrantyExpiry: '2025-01-09',
    warrantyStatus: 'active',
    returnPeriodExpiry: '2023-01-20',
    lifeScore: 85,
    hasReceipt: true,
    hasWarrantyCard: true,
    thumbnailIcon: 'Sparkles',
    description: 'Cordless stick vacuum cleaner with laser dust detection.',
    warrantyDetails: {
      provider: 'Dyson 2-Year Comprehensive',
      durationMonths: 24,
      inclusions: ['Motor unit', 'Battery failure', 'Laser head mechanism'],
      exclusions: ['Filter wear due to lack of washing']
    },
    maintenanceHistory: [
      { date: '2023-01-10', title: 'Registered with Dyson', type: 'system' },
      { date: '2024-02-01', title: 'HEPA Filter Washed', type: 'maintenance' }
    ]
  },
  {
    id: 'prod-5',
    name: 'LG 55" OLED 4K Smart TV',
    category: 'Electronics',
    brand: 'LG',
    model: 'OLED55C2PSC',
    serialNumber: 'LG-OLED-55-901',
    purchaseDate: '2021-11-25',
    purchasePrice: '₹1,15,000',
    store: 'Croma',
    warrantyExpiry: '2023-11-24',
    warrantyStatus: 'expired',
    returnPeriodExpiry: '2021-12-05',
    lifeScore: 78,
    hasReceipt: true,
    hasWarrantyCard: false,
    thumbnailIcon: 'Tv',
    description: 'Cinema HDR OLED 4K display with Dolby Vision and webOS.',
    warrantyDetails: {
      provider: 'LG 2-Year Panel Warranty',
      durationMonths: 24,
      inclusions: ['OLED Panel defects', 'Motherboard failure'],
      exclusions: ['Burn-in from static images left > 24hrs', 'Physical panel impact']
    },
    maintenanceHistory: [
      { date: '2021-11-25', title: 'Wall Mount Installed', type: 'service' },
      { date: '2023-11-24', title: 'Standard Warranty Ended', type: 'system' }
    ]
  }
];

export const mockDocuments = [
  {
    id: 'doc-1',
    title: 'Apple Store Tax Invoice #INV-8831',
    productName: 'Apple MacBook Pro 14"',
    type: 'Invoice / Receipt',
    format: 'PDF',
    size: '1.4 MB',
    uploadDate: '2024-03-15',
    ocrStatus: 'Extracted (100%)',
    thumbnail: '📄'
  },
  {
    id: 'doc-2',
    title: 'Sony India Warranty Certificate',
    productName: 'Sony WH-1000XM5 Headphones',
    type: 'Warranty Card',
    format: 'JPEG',
    size: '840 KB',
    uploadDate: '2023-10-20',
    ocrStatus: 'Extracted (100%)',
    thumbnail: '🛡️'
  },
  {
    id: 'doc-3',
    title: 'Reliance Digital Tax Bill #RD-0941',
    productName: 'Samsung 324L Refrigerator',
    type: 'Invoice / Receipt',
    format: 'PDF',
    size: '2.1 MB',
    uploadDate: '2022-08-05',
    ocrStatus: 'Extracted (100%)',
    thumbnail: '📄'
  },
  {
    id: 'doc-4',
    title: 'Dyson User Manual & Care Guide',
    productName: 'Dyson V12 Detect Vacuum',
    type: 'Manual',
    format: 'PDF',
    size: '4.8 MB',
    uploadDate: '2023-01-10',
    ocrStatus: 'Indexed for AI',
    thumbnail: '📘'
  }
];

export const mockAccessories = [
  {
    id: 'acc-1',
    title: 'Incase Compact Sleeve in Woolenex',
    productName: 'Apple MacBook Pro 14"',
    category: 'Protection Case',
    price: '₹4,990',
    compatibility: '100% Compatible (14-inch M-series)',
    store: 'Apple Online Store',
    tag: 'Recommended'
  },
  {
    id: 'acc-2',
    title: 'Replacement Cooling Gel Ear Cushions',
    productName: 'Sony WH-1000XM5 Headphones',
    category: 'Replacement Part',
    price: '₹1,499',
    compatibility: 'Exact Fit for WH-1000XM5',
    store: 'Amazon India',
    tag: 'Popular'
  },
  {
    id: 'acc-3',
    title: 'Dyson Post-Motor HEPA Replacement Filter',
    productName: 'Dyson V12 Detect Vacuum',
    category: 'Maintenance',
    price: '₹2,800',
    compatibility: 'Genuine Dyson V12 Slim part',
    store: 'Dyson India',
    tag: 'Essential'
  }
];

export const mockNotifications = [
  {
    id: 'notif-1',
    title: 'Warranty Expiring Soon',
    message: 'Sony WH-1000XM5 warranty expires in 14 days on 19-Oct-2024. Review claims if needed.',
    type: 'warning',
    date: '2 hours ago',
    unread: true
  },
  {
    id: 'notif-2',
    title: 'Maintenance Reminder',
    message: 'Dyson V12 HEPA filter is due for monthly cold water rinse for optimal suction.',
    type: 'info',
    date: '1 day ago',
    unread: true
  },
  {
    id: 'notif-3',
    title: 'Receipt Successfully Processed',
    message: 'OCR extracted MacBook Pro serial #C02G8393MD6T with 100% confidence.',
    type: 'success',
    date: '3 days ago',
    unread: false
  }
];

export const mockChatPresets = [
  'Is accidental drop covered under my MacBook warranty?',
  'How do I claim a replacement for my Sony Headphones?',
  'What is the recommended cleaning interval for my Dyson filter?',
  'Generate a formal warranty claim email to Samsung support.'
];
