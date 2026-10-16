# web-quality (режим A11Y) — WCAG-справочник, примеры фиксов и шаблон отчёта

> Вынесено из тела агента `testing/workers/accessibility-tester.md` 2026-08-20 — тело грузится при каждом спавне, справочник нужен только при написании отчёта.
> 2026-08-22 агент сведён в `testing/workers/web-quality.md` (режим A11Y); файл переименован из `accessibility-tester-report-template.md`, содержимое не менялось, кроме имени агента в шаблонах отчёта.

## WCAG Success Criteria Reference

### Level A (Critical)

- **1.1.1**: Non-text Content (alt text)
- **1.3.1**: Info and Relationships (semantic HTML, labels)
- **2.1.1**: Keyboard (all functionality via keyboard)
- **2.1.2**: No Keyboard Trap
- **2.4.1**: Bypass Blocks (skip links)
- **3.3.2**: Labels or Instructions (form labels)
- **4.1.2**: Name, Role, Value (ARIA)

### Level AA (High)

- **1.4.3**: Contrast (Minimum) - 4.5:1 for normal text
- **1.4.5**: Images of Text (avoid text in images)
- **2.4.7**: Focus Visible
- **2.5.5**: Target Size (44x44px minimum)
- **3.2.4**: Consistent Identification
- **3.3.3**: Error Suggestion

### Level AAA (Medium)

- **1.4.6**: Contrast (Enhanced) - 7:1 for normal text
- **2.1.3**: Keyboard (No Exception)
- **2.4.8**: Location (breadcrumbs, current page indicator)
- **2.5.6**: Concurrent Input Mechanisms

## Code Fix Examples

### Missing Alt Text
```jsx
// ❌ Bad
<img src="/photo.jpg" />

// ✅ Good
<img src="/photo.jpg" alt="Team member John Smith presenting at conference" />

// ✅ Decorative image
<img src="/decoration.svg" alt="" role="presentation" />
```

### Color Contrast
```css
/* ❌ Bad - Contrast ratio 3.2:1 */
.text {
  color: #999999;
  background: #ffffff;
}

/* ✅ Good - Contrast ratio 7.1:1 */
.text {
  color: #595959;
  background: #ffffff;
}
```

### Keyboard Navigation
```jsx
// ❌ Bad - div not keyboard accessible
<div onClick={handleClick}>Click me</div>

// ✅ Good - button is keyboard accessible
<button onClick={handleClick}>Click me</button>

// ✅ Alternative with div
<div
  onClick={handleClick}
  onKeyDown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabIndex={0}
>
  Click me
</div>
```

### ARIA Labels
```jsx
// ❌ Bad - icon button without label
<button><SearchIcon /></button>

// ✅ Good - proper ARIA label
<button aria-label="Search products">
  <SearchIcon />
</button>
```

### Focus Indicators
```css
/* ❌ Bad - focus indicator removed */
button:focus {
  outline: none;
}

/* ✅ Good - visible focus indicator */
button:focus-visible {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}
```

### Form Labels
```jsx
// ❌ Bad - no label
<input type="email" placeholder="Email" />

// ✅ Good - associated label
<label htmlFor="email">Email</label>
<input type="email" id="email" />

// ✅ Alternative - visually hidden label
<label htmlFor="email" className="sr-only">Email</label>
<input type="email" id="email" placeholder="Email" />
```

## Report Format

Generate report following this structure:

```markdown
---
report_type: accessibility-audit
generated: 2025-11-10T15:00:00Z
version: 2025-11-10
status: success
agent: web-quality
duration: 8m 45s
wcag_level: AA
compliance_score: 72
issues_found: 23
critical_count: 3
high_count: 8
medium_count: 10
low_count: 2
---

# Accessibility Audit Report: 2025-11-10

**Generated**: 2025-11-10 15:00:00 UTC
**Status**: ⚠️ PARTIAL
**WCAG Level**: AA
**Compliance Score**: 72/100
**Agent**: web-quality (режим A11Y)
**Duration**: 8m 45s

---

## Executive Summary

Comprehensive accessibility audit completed. Found 23 issues requiring attention to meet WCAG 2.1 Level AA compliance.

### Key Metrics

- **WCAG Compliance Score**: 72/100 (Needs Improvement)
- **Level AA Status**: ⚠️ PARTIAL COMPLIANCE
- **Critical Issues (Level A)**: 3 (Blocking)
- **High Priority (Level AA)**: 8 (Required for AA)
- **Medium Priority (Level AAA)**: 10 (Enhancement)
- **Low Priority**: 2 (Best Practices)

### Highlights

- ❌ 3 critical accessibility blockers (Level A failures)
- ⚠️ 8 high priority issues prevent Level AA compliance
- ✅ Keyboard navigation generally functional
- ✅ Semantic HTML structure mostly correct
- ❌ Color contrast fails on 5 elements
- ⚠️ Missing ARIA labels on 12 interactive elements

---

## Detailed Findings

### Critical Issues (Level A - Blocking) 🔴

#### 1. Missing Alt Text on Team Photos

- **WCAG Criterion**: 1.1.1 Non-text Content (Level A)
- **Severity**: Critical
- **Location**: `src/components/TeamMemberCard.tsx`
- **Issue**: 8 team member photos missing descriptive alt text
- **Impact**: Screen reader users cannot identify team members
- **Current Code**:
  ```jsx
  <img src="/team-photo/john-smith.jpg" />
  ```
- **Fix**:
  ```jsx
  <img
    src="/team-photo/john-smith.jpg"
    alt="John Smith, Senior Software Engineer"
  />
  ```
- **Priority**: P0 (Fix immediately)
- **Estimated Time**: 15 minutes

#### 2. Keyboard Trap in Modal Dialog

- **WCAG Criterion**: 2.1.2 No Keyboard Trap (Level A)
- **Severity**: Critical
- **Location**: `src/components/Modal.tsx`
- **Issue**: Users cannot close modal with keyboard (Escape key not handled)
- **Impact**: Keyboard-only users trapped in modal
- **Current Code**:
  ```jsx
  <div className="modal" onClick={onClose}>
    {children}
  </div>
  ```
- **Fix**:
  ```jsx
  <div
    className="modal"
    onClick={onClose}
    onKeyDown={(e) => e.key === 'Escape' && onClose()}
    role="dialog"
    aria-modal="true"
  >
    {children}
  </div>
  ```
- **Priority**: P0 (Fix immediately)
- **Estimated Time**: 20 minutes

#### 3. Form Inputs Missing Labels

- **WCAG Criterion**: 3.3.2 Labels or Instructions (Level A)
- **Severity**: Critical
- **Location**: `src/components/ContactForm.tsx`
- **Issue**: Email and message inputs missing associated labels
- **Impact**: Screen reader users don't know what to enter
- **Current Code**:
  ```jsx
  <input type="email" placeholder="Your email" />
  <textarea placeholder="Your message" />
  ```
- **Fix**:
  ```jsx
  <label htmlFor="email">Email Address</label>
  <input type="email" id="email" placeholder="Your email" />

  <label htmlFor="message">Message</label>
  <textarea id="message" placeholder="Your message" />
  ```
- **Priority**: P0 (Fix immediately)
- **Estimated Time**: 10 minutes

### High Priority Issues (Level AA Required) 🟡

#### 4. Low Color Contrast on Navigation Links

- **WCAG Criterion**: 1.4.3 Contrast (Minimum) (Level AA)
- **Severity**: High
- **Location**: `src/components/Navigation.tsx`
- **Issue**: Navigation links have contrast ratio of 3.2:1 (minimum 4.5:1)
- **Impact**: Users with low vision cannot read navigation text
- **Current CSS**:
  ```css
  .nav-link {
    color: #999999;
    background: #ffffff;
  }
  ```
- **Fix**:
  ```css
  .nav-link {
    color: #595959; /* Contrast ratio: 7.1:1 */
    background: #ffffff;
  }
  ```
- **Priority**: P1 (Required for AA)
- **Estimated Time**: 5 minutes

#### 5. Touch Targets Too Small on Mobile

- **WCAG Criterion**: 2.5.5 Target Size (Level AAA recommended, Level AA from 2.5.8)
- **Severity**: High
- **Location**: Social media icons in footer
- **Issue**: Icon buttons are 32x32px (minimum 44x44px)
- **Impact**: Users on mobile devices have difficulty tapping accurately
- **Current CSS**:
  ```css
  .social-icon {
    width: 32px;
    height: 32px;
  }
  ```
- **Fix**:
  ```css
  .social-icon {
    width: 44px;
    height: 44px;
    padding: 6px; /* Increased touch area */
  }
  ```
- **Priority**: P1 (Required for AA)
- **Estimated Time**: 10 minutes

[... Additional high priority issues ...]

### Medium Priority Issues (Level AAA / Best Practices) 🟢

[... Medium priority issues ...]

### Low Priority Issues (Enhancements) 🔵

[... Low priority issues ...]

---

## Validation Results

### Type Check

**Command**: `pnpm type-check`

**Status**: ✅ PASSED

**Output**:
\```
tsc --noEmit
No type errors found.
\```

**Exit Code**: 0

### Build

**Command**: `pnpm build`

**Status**: ✅ PASSED

**Output**:
\```
next build
✓ Compiled successfully
\```

**Exit Code**: 0

### Overall Status

**Validation**: ⚠️ PARTIAL

Accessibility issues found but build is stable. Must fix Level A critical issues to meet minimum accessibility standards.

---

## Next Steps

### Immediate Actions (P0 - Critical)

1. **Add alt text to all team member photos** (15 min)
   - Update TeamMemberCard component
   - Use descriptive alt text with name and role
   - Test with screen reader

2. **Fix keyboard trap in modal dialog** (20 min)
   - Add Escape key handler
   - Implement focus trap
   - Test keyboard navigation

3. **Add labels to form inputs** (10 min)
   - Associate labels with inputs using htmlFor/id
   - Test with screen reader
   - Verify label announcements

### High Priority Actions (P1 - Level AA Required)

4. **Improve color contrast** (5 min per element)
   - Update navigation link colors
   - Test button text contrast
   - Verify with contrast checker tool

5. **Increase touch target sizes** (10 min)
   - Update social media icon sizes
   - Add adequate padding/spacing
   - Test on mobile device

6. **Add ARIA labels to icon buttons** (15 min)
   - Search, menu, close buttons
   - Test with screen reader
   - Verify announcements

### Recommended Actions (This Sprint)

- Run automated accessibility testing in CI/CD
- Add axe-core or similar testing library
- Conduct screen reader testing (NVDA/JAWS)
- Train team on accessibility best practices

### Follow-Up

- Schedule quarterly accessibility audits
- Set up automated accessibility monitoring
- Consider accessibility review in code review process
- Document accessibility guidelines in style guide

---

## Screenshots

1. `accessibility-baseline-desktop.png` - Desktop viewport (1920x1080)
2. `accessibility-mobile-small.png` - iPhone SE (375x667)
3. `accessibility-mobile-medium.png` - iPhone 14 Pro (393x852)
4. `accessibility-tablet.png` - iPad Mini (768x1024)

---

## Testing Environment

- **Browser**: Chromium (via Playwright)
- **Viewports Tested**: Desktop (1920x1080), Mobile (375x667, 393x852), Tablet (768x1024)
- **WCAG Level**: 2.1 Level AA (with AAA recommendations)
- **Tools Used**: Playwright, Browser DevTools, Manual Testing
- **Testing Date**: 2025-11-10

---

## Appendix: WCAG 2.1 Success Criteria Summary

### Level A (Must Pass)
- 1.1.1 Non-text Content
- 2.1.1 Keyboard
- 2.1.2 No Keyboard Trap
- 3.3.2 Labels or Instructions
- 4.1.2 Name, Role, Value

### Level AA (Required for Compliance)
- 1.4.3 Contrast (Minimum) - 4.5:1
- 2.4.7 Focus Visible
- 2.5.5 Target Size - 44x44px

### Level AAA (Best Practices)
- 1.4.6 Contrast (Enhanced) - 7:1
- 2.1.3 Keyboard (No Exception)

---

**Report Version**: 1.0
**Agent**: web-quality (режим A11Y)
**Next Review**: After critical fixes implemented
```
