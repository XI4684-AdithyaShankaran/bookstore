module.exports = {
  extends: [
    'stylelint-config-standard',
    'stylelint-config-tailwindcss'
  ],
  rules: {
    'at-rule-no-unknown': null,
    // Allow inline styles for virtualization components
    'declaration-no-important': null
  },
  // Ignore files that use react-window or other virtualization libraries
  // These libraries require inline styles for proper positioning
  ignoreFiles: [
    '**/VirtualBookGrid.tsx',
    '**/StreamingBookGrid.tsx',
    '**/BookshelfCard.tsx',
    '**/*Virtual*.tsx',
    '**/*Streaming*.tsx'
  ]
}; 