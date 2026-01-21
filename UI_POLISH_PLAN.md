# 🎨 UI Polish Plan - Matching Reference Design

## 📊 Issues Identified

### Title & Text Spacing
- ❌ Too much gap between title and metadata
- ❌ Too much gap between metadata and content
- ❌ Inconsistent line heights
- ❌ Text sizes not matching reference

### Note Cards
- ❌ Title too large
- ❌ Preview text too small
- ❌ Timestamp positioning off
- ❌ Thumbnail size inconsistent
- ❌ Card padding too loose

### Typography
- ❌ Font weights not matching
- ❌ Line heights too loose
- ❌ Letter spacing needs adjustment
- ❌ Color contrast could be better

### Spacing System
- ❌ No consistent spacing scale
- ❌ Gaps are arbitrary
- ❌ Padding inconsistent

## 🎯 Reference Design Analysis

### Editor (Right Pane)
```
Title: 32px, bold, mb-2 (8px)
Metadata: 12px, gray-500, mb-4 (16px)
Content: 14px, line-height 1.6, gray-200
```

### Note Cards (Middle Feed)
```
Card padding: 12px
Thumbnail: 48px × 48px, rounded-md
Title: 13px, medium, mb-0.5 (2px)
Preview: 12px, gray-400, line-clamp-2, mb-1 (4px)
Tags: 11px, tight spacing
Time: 11px, gray-500
```

### Sidebar
```
Section title: 11px, uppercase, gray-600
Items: 13px, medium
Tags: 11px, rounded-full
```

## 🔧 Fixes Needed

### 1. Typography Scale
```css
xs:   11px  (tags, timestamps)
sm:   12px  (metadata, preview)
base: 13px  (titles, nav items)
lg:   14px  (content)
xl:   16px  (section headers)
2xl:  32px  (page title)
```

### 2. Spacing Scale
```css
0.5: 2px   (tight gaps)
1:   4px   (small gaps)
1.5: 6px   (medium gaps)
2:   8px   (default gaps)
3:   12px  (card padding)
4:   16px  (section spacing)
```

### 3. Line Heights
```css
tight:  1.25  (titles)
normal: 1.5   (body text)
relaxed: 1.6  (content)
```

## 📝 Implementation Plan

### Phase 1: Typography System
- Create consistent font size scale
- Fix line heights
- Adjust font weights

### Phase 2: Spacing System
- Implement 4px base spacing
- Fix all margins/paddings
- Consistent gaps

### Phase 3: Component Polish
- Note cards refinement
- Editor layout fixes
- Sidebar improvements

### Phase 4: Color Refinement
- Better text contrast
- Subtle hover states
- Proper disabled states

## 🎨 Design Tokens

```typescript
// Typography
const fontSize = {
  xs: '11px',
  sm: '12px',
  base: '13px',
  lg: '14px',
  xl: '16px',
  '2xl': '32px',
}

const lineHeight = {
  tight: '1.25',
  normal: '1.5',
  relaxed: '1.6',
}

const fontWeight = {
  normal: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
}

// Spacing (4px base)
const spacing = {
  0.5: '2px',
  1: '4px',
  1.5: '6px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
}

// Colors
const colors = {
  bg: {
    primary: '#1e1e1e',
    secondary: '#252525',
    tertiary: '#2d2d2d',
  },
  text: {
    primary: '#e4e4e4',
    secondary: '#a0a0a0',
    tertiary: '#707070',
  },
  border: {
    default: '#3a3a3a',
    subtle: '#2a2a2a',
  }
}
```

## ✅ Next Steps

1. Update NoteEditor with proper spacing
2. Refine NoteCard typography
3. Polish Sidebar elements
4. Add proper line-clamp utilities
5. Test all spacing combinations

Let me implement these fixes now...
