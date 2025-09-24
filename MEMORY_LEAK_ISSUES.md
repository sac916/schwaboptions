# Memory Leak Issues - SchwaOptions

**Date**: 2025-09-24
**Status**: ✅ RESOLVED - Balanced approach implemented
**Impact**: Memory leaks in React components during state updates

## Issue Details

### 1. React State Update on Unmounted Component
**Error**: `Warning: Can't perform a React state update on an unmounted component. This is a no-op, but it indicates a memory leak in your application.`

**Stack Trace**:
```
Component lifecycle: t > t > div > t > t > t > Suspense > CheckedComponent > BaseTreeContainer > ComponentErrorBoundary > DashWrapper
Location: index.tsx:31 - setTimeout callback
```

**Root Cause**: Component is updating state after being unmounted, typically caused by:
- Async operations (setTimeout/setInterval) not cleaned up
- API calls continuing after component unmount
- Event listeners not removed in componentWillUnmount

### 2. Plotly Canvas Performance Warning
**Error**: `Canvas2D: Multiple readback operations using getImageData are faster with the willReadFrequently attribute set to true`

**Impact**: Performance degradation in chart rendering
**Location**: plotly.min.js:8

## Immediate Actions Required

### High Priority (Fix Today)
1. **Component Cleanup**: Add proper componentWillUnmount cleanup
2. **Async Operation Cancellation**: Cancel all timers and API calls
3. **Event Listener Removal**: Remove all event listeners on unmount
4. **Plotly Canvas Optimization**: Add willReadFrequently attribute

### Medium Priority (Fix This Week)
1. **Memory Profiling**: Monitor memory usage patterns
2. **Component Lifecycle Audit**: Review all components for proper cleanup
3. **State Management Review**: Ensure proper state cleanup

## Technical Details

### Affected Files
- `index.tsx` (line 31 - setTimeout issue)
- Plotly components (canvas performance)
- Base Dash components (React lifecycle)

### Memory Leak Vectors
1. **Timer Leaks**: setTimeout/setInterval not cleared
2. **Event Listener Leaks**: DOM events not removed
3. **API Request Leaks**: Ongoing requests after unmount
4. **State Update Leaks**: setState after component destroyed

## Fix Strategy - IMPLEMENTED ✅

### 1. Balanced Cleanup Approach
```javascript
// Implemented in dash_app.py clientside callback:

// 1. Track timeouts without interfering with callbacks
window.setTimeout = function(callback, delay) {
    const id = window.originalSetTimeout(callback, delay);
    window.dashTimeouts.push(id);
    return id;
};

// 2. Clean up tracked timeouts on component changes
window.dashTimeouts.forEach(id => clearTimeout(id));
window.dashTimeouts = [];

// 3. Canvas performance optimization
document.querySelectorAll('canvas').forEach(canvas => {
    canvas.setAttribute('willReadFrequently', 'true');
});
```

### 2. Plotly Canvas Fix
```javascript
// Add to plotly config
config: {
    toImageButtonOptions: {
        willReadFrequently: true
    }
}
```

## Monitoring

### Memory Leak Detection
1. **Browser DevTools**: Memory tab profiling
2. **React DevTools**: Component render tracking
3. **Performance Monitoring**: Regular memory usage checks

### Key Metrics to Track
- Memory usage over time
- Component mount/unmount cycles
- Timer and interval creation/cleanup
- Event listener count

## Prevention

### Code Review Checklist
- [ ] All setTimeout/setInterval have clearTimeout/clearInterval
- [ ] All event listeners have corresponding removeEventListener
- [ ] All API requests can be cancelled on unmount
- [ ] All subscriptions are unsubscribed in cleanup
- [ ] Component state is not updated after unmount

### Development Standards
1. **Always implement componentWillUnmount** for components with:
   - Timers
   - Event listeners
   - API calls
   - Subscriptions

2. **Use AbortController** for all fetch requests
3. **Use cleanup functions** in React hooks
4. **Test component unmounting** in development

## Risk Assessment

**Current Risk Level**: 🚨 HIGH
- Memory leaks can cause browser crashes
- Performance degradation over time
- Potential data corruption
- User experience issues

**Business Impact**:
- Application instability
- Increased support requests
- Potential data loss
- Professional reputation risk

---

**Next Steps**: Implement fixes immediately, then establish monitoring and prevention protocols.

**Owner**: Development Team
**Reviewer**: Security/QA Team
**Due Date**: End of day today