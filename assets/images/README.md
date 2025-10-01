# Image Assets

This directory contains optimized image assets for the Free Programming Books project.

## Badge Images

- `awesome-badge.svg` - Local version of the Awesome badge (replaces cdn.rawgit.com dependency)
- `license-badge.svg` - Local version of the CC BY 4.0 license badge
- `hacktoberfest-badge.svg` - Local version of the Hacktoberfest 2025 badge

## Optimization Features

- **SVG Format**: All badges are in SVG format for scalability and small file sizes
- **Local Hosting**: No external dependencies on potentially unreliable CDNs
- **Optimized Code**: Clean, minimal SVG code for fast loading
- **Accessibility**: Proper contrast ratios and semantic markup

## Performance Benefits

1. **Faster Loading**: Local images load faster than external CDN requests
2. **Reliability**: No dependency on external services that may go down
3. **Consistency**: Guaranteed visual consistency across all environments
4. **Offline Support**: Images work even when external services are unavailable

## Usage

These images are automatically included in the project via the Jekyll configuration and custom CSS. The images are preloaded for optimal performance.

## Maintenance

When updating badges:
1. Ensure SVG code is optimized and clean
2. Maintain consistent styling with the project theme
3. Test across different browsers and devices
4. Verify accessibility compliance
