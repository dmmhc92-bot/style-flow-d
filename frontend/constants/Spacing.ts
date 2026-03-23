// Premium 8pt Grid Spacing System
// Apple-quality consistent spacing throughout

export default {
  // Base 8pt grid
  xs: 4,      // 0.5x
  sm: 8,      // 1x (base unit)
  md: 16,     // 2x
  lg: 24,     // 3x
  xl: 32,     // 4x
  xxl: 48,    // 6x
  xxxl: 64,   // 8x
  
  // Screen-level spacing
  screenPadding: 16,    // Consistent screen edge padding
  cardPadding: 16,      // Internal card padding
  sectionSpacing: 24,   // Between major sections
  itemSpacing: 12,      // Between list items
  
  // Touch targets (Apple HIG: 44pt minimum)
  minTouchTarget: 44,
  touchTargetLarge: 48,
  
  // Border radius - Consistent rounded corners
  radiusXs: 4,          // Subtle rounding
  radiusSmall: 8,       // Small elements (chips, badges)
  radiusMedium: 12,     // Medium elements (inputs, buttons)
  radiusLarge: 16,      // Cards, modals
  radiusXL: 20,         // Large cards
  radiusXXL: 24,        // Hero elements
  radiusFull: 9999,     // Circular
  
  // Consistent component heights
  buttonHeight: 48,
  inputHeight: 48,
  headerHeight: 56,
  tabBarHeight: 60,
  
  // Icon sizes
  iconSmall: 16,
  iconMedium: 20,
  iconLarge: 24,
  iconXL: 32,
};