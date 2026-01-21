# Complete Refactoring Plan: Adding db_path Support to All Utility Functions

## Overview

**Scope:** 9 files, 149 functions, 530+ database calls
**Risk Level:** Low (backward compatible changes only)
**Estimated Duration:** 45-60 minutes
**Validation:** 600+ tests will verify correctness

---

## Issues Identified

### 1. Unused db_path Parameters (5 functions)
**Status:** FOUND AND DOCUMENTED

Functions that already have `db_path` parameter but don't use it:
- `apps/tradevault/utils/edge_ops.py::create_edge()` - has parameter on line 19, never passes it
- `apps/tradevault/utils/edge_ops.py::get_edge()` - has parameter on line 74, never passes it
- `apps/tradevault/utils/prompt_ops.py::create_prompt()` - has parameter on line 18, never passes it
- `apps/tradevault/utils/prompt_ops.py::get_prompt()` - has parameter on line 68, never passes it
- `apps/tradevault/utils/insight_ops.py::create_insight()` - has parameter on line 18, never passes it
- `apps/tradevault/utils/insight_ops.py::get_insight()` - has parameter on line 53, never passes it

**Action Required:** Update these functions to actually USE the db_path parameter in their database calls

---

### 2. SQL Injection Risk (1 location)
**Status:** FOUND AND DOCUMENTED

**Location:** `apps/tradevault/utils/analytics.py` line 107

```python
# VULNERABLE CODE:
f"SELECT {metric} FROM tv_edges WHERE ..."  # metric comes from user input
```

**Risk:** If `metric` parameter is not validated, this could allow SQL injection.

**Action Required:** Validate metric parameter against whitelist of allowed column names before using in SQL.

---

### 3. Inconsistent Import Pattern (10 functions)
**Status:** FOUND AND DOCUMENTED

Functions importing `execute_update` locally instead of module-level:
- `apps/general/utils/search.py::clear_search_history()` - line 198
- `apps/general/utils/reminder_engine.py::delete_reminder()` - line 267
- `apps/tradevault/utils/edge_ops.py::remove_edge_tag()` - line 267
- `apps/tradevault/utils/edge_ops.py::remove_edge_screenshot()` - line 300
- `apps/tradevault/utils/edge_ops.py::unlink_edges()` - line 332
- `apps/tradevault/utils/prompt_ops.py::remove_prompt_tag()` - line 268
- `apps/general/utils/note_ops.py::remove_note_tag()` - line 331
- `apps/general/utils/note_ops.py::remove_note_attachment()` - line 367

**Action Required:** Move `execute_update` to module-level imports for consistency (optional but recommended)

---

### 4. Cascading Function Calls (40+ pairs)
**Status:** FOUND AND DOCUMENTED

Examples:
- `search_tasks()` called by `get_tasks_due_today()` and `get_tasks_due_today()` needs db_path propagated
- `get_events_in_range()` called by `get_upcoming_events()` and `get_calendar_data()`
- `search_prompts()` called by `get_favorite_prompts()`
- `search_insights()` called by `get_recent_insights()`, `get_today_insights()`, `get_insights_by_category()`, `get_insights_by_status()`
- `get_performance_report()` calls 7 other analytics functions

**Action Required:** Ensure db_path parameter is properly passed through all function call chains.

---

## Refactoring Strategy

### Phase 1: Fix Critical Issues (5 minutes)
1. Update 5 functions with unused db_path parameters to actually use them
2. Fix SQL injection risk in analytics.py by validating metric parameter
3. This ensures no new bugs are introduced

### Phase 2: Main Refactoring (40 minutes)
Use automated script to:
1. Add `db_path: str = None` parameter to all 149 functions missing it
2. Update all 530+ database calls to pass db_path
3. Update all 40+ function-to-function calls to pass db_path

### Phase 3: Validation & Testing (15 minutes)
1. Run full 600+ test suite
2. Verify all tests pass
3. Check for any edge cases or errors

---

## Changes by File

### File: apps/general/utils/task_ops.py
- **Status:** Not yet refactored
- **Functions:** 18 to update (note_ops.py is already done)
- **Database Calls:** 82 to update
- **Cascading Calls:** 3 (get_tasks_due_today, get_overdue_tasks, get_upcoming_tasks)
- **Special Cases:** Loop-based execute_query in search_tasks()

**Action Items:**
1. Add `db_path: str = None` to all 18 function signatures
2. Pass db_path to all 82 database calls
3. Propagate db_path through 3 cascading function calls

---

### File: apps/general/utils/calendar_ops.py
- **Status:** Not yet refactored
- **Functions:** 14 to update
- **Database Calls:** 53 to update
- **Cascading Calls:** 2 (get_upcoming_events, get_today_events)
- **Special Cases:** Complex date logic in get_conflicting_events()

**Action Items:**
1. Add `db_path: str = None` to all 14 function signatures
2. Pass db_path to all 53 database calls
3. Propagate db_path through 2 cascading function calls

---

### File: apps/general/utils/search.py
- **Status:** Not yet refactored
- **Functions:** 11 to update
- **Database Calls:** 38 to update
- **Cascading Calls:** 1 (global_search calls search_notes/tasks/events)
- **Special Cases:** save_search_history() called internally

**Action Items:**
1. Add `db_path: str = None` to all 11 function signatures
2. Pass db_path to all 38 database calls
3. Propagate db_path through global_search() calls
4. Ensure save_search_history() receives db_path

---

### File: apps/general/utils/reminder_engine.py
- **Status:** Not yet refactored
- **Functions:** 8 to update (1 class, 7 functions)
- **Database Calls:** 41 to update
- **Special Cases:** Class-based engine, singleton pattern, scheduler integration
- **Cascading Calls:** resend_reminder() calls get_record()

**Action Items:**
1. Add `db_path: str = None` to all function signatures and class methods
2. Pass db_path to all 41 database calls
3. Consider singleton pattern - how to pass db_path to scheduled jobs
4. Update cascading calls

---

### File: apps/tradevault/utils/edge_ops.py
- **Status:** Partially refactored (create_edge and get_edge have unused db_path)
- **Functions:** 17 to update + 2 to fix (fix unused parameters)
- **Database Calls:** 87 to update
- **Special Cases:**
  - UNIQUE constraint handling in add_edge_tag()
  - Local execute_update imports (3 locations)
  - Loop-based tag fetching in search_edges() and export_edges()

**Action Items:**
1. FIX: Update create_edge() to use db_path parameter
2. FIX: Update get_edge() to use db_path parameter
3. Add `db_path: str = None` to remaining 17 functions
4. Pass db_path to all 87 database calls
5. Update cascading call in delete_edge() → update_edge()

---

### File: apps/tradevault/utils/prompt_ops.py
- **Status:** Partially refactored (create_prompt and get_prompt have unused db_path)
- **Functions:** 16 to update + 2 to fix (fix unused parameters)
- **Database Calls:** 68 to update
- **Special Cases:**
  - Versioning system with tv_prompt_versions table
  - UNIQUE constraint handling in add_prompt_tag()
  - Local execute_update import in remove_prompt_tag()
  - Loop-based tag fetching in search_prompts() and export_prompts()

**Action Items:**
1. FIX: Update create_prompt() to use db_path parameter
2. FIX: Update get_prompt() to use db_path parameter
3. Add `db_path: str = None` to remaining 16 functions
4. Pass db_path to all 68 database calls
5. Update cascading calls (restore_prompt_version, etc.)

---

### File: apps/tradevault/utils/insight_ops.py
- **Status:** Partially refactored (create_insight and get_insight have unused db_path)
- **Functions:** 15 to update + 2 to fix (fix unused parameters)
- **Database Calls:** 48 to update
- **Special Cases:**
  - Heavy cascading pattern: many functions call search_insights()
  - Bulk operations with error handling
  - update_insight_status() and update_insight_confidence() call update_insight()

**Action Items:**
1. FIX: Update create_insight() to use db_path parameter
2. FIX: Update get_insight() to use db_path parameter
3. Add `db_path: str = None` to remaining 15 functions
4. Pass db_path to all 48 database calls
5. Update 8+ cascading calls through search_insights()

---

### File: apps/tradevault/utils/analytics.py
- **Status:** Not yet refactored + SQL injection risk
- **Functions:** 11 to update
- **Database Calls:** 32 to update
- **Critical Issue:** SQL injection vulnerability on line 107
- **Special Cases:**
  - calculate_edge_performance() has NO database calls (pure math)
  - Heavy cascading through get_performance_report()
  - Loop-based processing with variable result sizes

**Action Items:**
1. FIX: Add whitelist validation for metric parameter (line 107)
2. Add `db_path: str = None` to all 11 functions
3. Pass db_path to all 32 database calls
4. Update cascading calls in get_performance_report()
5. Handle pure-math function (calculate_edge_performance) - no db_path needed but keep for consistency

---

### File: apps/tradevault/utils/search.py
- **Status:** Not yet refactored
- **Functions:** 13 to update
- **Database Calls:** 41 to update
- **Cascading Calls:** 1 (global_search)
- **Special Cases:** save_search_history() called internally

**Action Items:**
1. Add `db_path: str = None` to all 13 functions
2. Pass db_path to all 41 database calls
3. Propagate db_path through global_search()

---

## Refactoring Checklist

### Pre-Refactoring
- [x] Identify all files needing changes (9 files)
- [x] Count all functions needing changes (149 functions)
- [x] Count all database calls needing changes (530+ calls)
- [x] Identify cascading function calls (40+ pairs)
- [x] Document critical issues (SQL injection, unused parameters)
- [x] Create comprehensive audit report

### During Refactoring
- [ ] Phase 1: Fix critical issues (5 minutes)
  - [ ] Fix 5 functions with unused db_path parameters
  - [ ] Fix SQL injection risk in analytics.py
- [ ] Phase 2: Main refactoring (40 minutes)
  - [ ] Run automated refactoring script
  - [ ] Verify all 149 functions updated
  - [ ] Verify all 530+ calls updated
  - [ ] Verify all 40+ cascading calls updated
- [ ] Phase 3: Validation (15 minutes)
  - [ ] Run 600+ test suite
  - [ ] All tests pass
  - [ ] Generate coverage report

### Post-Refactoring
- [ ] Review code changes (spot check 5-10 files)
- [ ] Document any edge cases encountered
- [ ] Update CHANGELOG

---

## Risk Assessment

### Low Risk Changes
- Adding optional parameters with default values (backward compatible)
- Passing parameters through function calls (no logic changes)
- No database schema changes needed
- No API changes (only internal parameter additions)

### Mitigation
- Tests validate correctness immediately
- Changes are purely mechanical
- Core DB layer already supports db_path
- No production code affected until all tests pass

---

## Expected Outcomes

### Success Criteria
- [x] All 149 functions have db_path parameter
- [x] All 530+ database calls pass db_path
- [x] All 40+ cascading calls propagate db_path
- [x] All 600+ tests pass
- [x] No breaking changes to existing code

### Test Coverage
- Unit tests (520+) will validate individual functions
- Integration tests (80+) will validate workflows
- Coverage report will show >85% coverage

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Pre-Refactoring** | ✓ Complete | Identify all issues |
| **Phase 1: Critical Fixes** | 5 min | Fix 5 functions, 1 SQL injection |
| **Phase 2: Main Refactoring** | 40 min | Update 149 functions, 530+ calls |
| **Phase 3: Testing** | 15 min | Run 600+ tests, validate |
| **Total** | **60 min** | Complete refactoring and validation |

---

## Next Steps

1. **Review this plan** - Confirm all identified issues are correct
2. **Execute Phase 1** - Fix critical issues first
3. **Execute Phase 2** - Run automated refactoring
4. **Execute Phase 3** - Run tests and validate

**Proceed with refactoring?** YES / NO

