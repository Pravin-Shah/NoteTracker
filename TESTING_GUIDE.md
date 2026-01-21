# NoteTracker Testing Guide

**Complete guide to running, writing, and maintaining tests for NoteTracker**

---

## Overview

The NoteTracker project includes **600+ automated tests** organized into:

- **Unit Tests** (~520 tests) - Fast, isolated tests for individual functions
- **Integration Tests** (~80 tests) - Cross-layer tests for complete workflows
- **Configuration** - pytest, CI/CD, and test runner setup

---

## Quick Start

### Run All Tests

```bash
python run_tests.py all
```

### Run Specific Test Suite

```bash
# Unit tests only
python run_tests.py unit

# Integration tests only
python run_tests.py integration

# With coverage analysis
python run_tests.py coverage

# Quick smoke tests
python run_tests.py smoke
```

### Run Tests for Specific Module

```bash
python run_tests.py module note_ops
```

### Run Specific Test File

```bash
python run_tests.py specific unit/test_note_ops.py
```

---

## Test Organization

```
tests/
├── conftest.py                          # Shared fixtures (235 LOC)
├── unit/                                # Unit tests (520+ tests)
│   ├── test_note_ops.py                 # Note CRUD, tags, search (48 tests)
│   ├── test_task_ops.py                 # Task management (50 tests)
│   ├── test_calendar_ops.py             # Calendar events (40 tests)
│   ├── test_search_general.py           # General app search (40 tests)
│   ├── test_edge_ops.py                 # Edge management (50 tests)
│   ├── test_prompt_ops.py               # Prompt templates (45 tests)
│   ├── test_insight_ops.py              # Insights (45 tests)
│   ├── test_analytics.py                # Analytics (40 tests)
│   └── test_search_tradevault.py        # TradeVault search (40 tests)
├── integration/                         # Integration tests (80+ tests)
│   └── test_ui_backend_integration.py   # UI ↔ Backend workflows (80+ tests)
└── pytest.ini                           # Pytest configuration

Total: 600+ Tests
```

---

## Test Files Overview

### Core Infrastructure Tests (from Phase 1)

#### test_db.py (25 tests)
- Database initialization and connection
- Table creation and schema validation
- CRUD operations for all entity types
- Query execution and error handling
- Transaction management and rollback
- Foreign key constraint enforcement

#### test_auth.py (28 tests)
- User registration and login
- Password hashing and verification
- Session management
- Account activation/deactivation
- Password change operations
- Input validation and security

### General App Tests (Phase 2)

#### test_note_ops.py (48 tests)
**Test Classes:**
- TestNoteCreation - Valid data, missing fields, defaults
- TestNoteRetrieval - Get by ID, invalid ID, wrong user, tags
- TestNoteUpdate - Update title, content, importance
- TestNotePin - Pin/unpin operations
- TestNoteDelete - Delete operations, permissions
- TestNoteSearch - Search by title, content, category
- TestNoteTags - Add/remove tags, get tags
- TestNoteStatistics - Statistics, categories
- TestNoteExport - Export notes
- TestNoteBulkOperations - Bulk operations
- TestNoteImportance - Importance levels

#### test_task_ops.py (~50 tests)
**Test Classes:**
- TestTaskCreation - Valid data, validation, defaults
- TestTaskRetrieval - Get by ID, status filtering
- TestTaskUpdate - Update title, priority, status
- TestTaskStatusTransitions - Pending → In Progress → Completed
- TestTaskDueDates - Today, overdue, upcoming
- TestTaskDelete - Delete, permissions
- TestTaskSearch - Search by title, status, priority
- TestTaskTags - Tag operations
- TestTaskReminders - Reminder setup and tracking
- TestTaskChecklists - Checklist items
- TestTaskStatistics - Statistics and summaries

#### test_calendar_ops.py (~40 tests)
**Test Classes:**
- TestEventCreation - Valid data, date validation
- TestEventRetrieval - Get by ID, date range
- TestEventUpdate - Update title, dates, times
- TestEventDelete - Delete operations
- TestEventSearch - Search by title, category, date range
- TestEventConflicts - Conflict detection
- TestEventStatistics - Event statistics
- TestEventRecurrence - Recurring events (if implemented)

#### test_search_general.py (~40 tests)
**Test Classes:**
- TestNoteSearch - Full-text note search
- TestTaskSearch - Full-text task search
- TestEventSearch - Full-text event search
- TestCrossItemSearch - Global search across types
- TestSearchHistory - Save/retrieve search history
- TestSearchSuggestions - Search suggestions and autocomplete
- TestSearchFilters - Filter by category, date, status

### TradeVault App Tests (Phase 3)

#### test_edge_ops.py (~50 tests)
**Test Classes:**
- TestEdgeCreation - Valid data, validation
- TestEdgeRetrieval - Get by ID, filtering
- TestEdgeUpdate - Update performance metrics, status
- TestEdgeDelete - Delete operations
- TestEdgeSearch - Search by title, category, performance
- TestEdgeTags - Tag operations
- TestEdgeRelationships - Link/unlink related edges
- TestEdgeStatistics - Performance statistics
- TestTopPerformers - Identify best performing edges

#### test_prompt_ops.py (~45 tests)
**Test Classes:**
- TestPromptCreation - Valid data, validation
- TestPromptRetrieval - Get by ID, filtering
- TestPromptUpdate - Update with versioning
- TestPromptVersioning - Version history, restore
- TestPromptSearch - Search by title, category
- TestPromptFavorites - Mark/unmark favorites
- TestPromptUsage - Track usage statistics
- TestPromptTags - Tag operations
- TestPromptExport - Export prompts

#### test_insight_ops.py (~45 tests)
**Test Classes:**
- TestInsightCreation - Valid data, validation
- TestInsightRetrieval - Get by ID, filtering
- TestInsightUpdate - Update description, category
- TestInsightStatus - Open/Confirmed/Disputed transitions
- TestInsightConfidence - Confidence levels
- TestInsightSearch - Search operations
- TestInsightDelete - Delete operations
- TestInsightStatistics - Statistics by status/confidence
- TestInsightBulkOperations - Bulk updates

#### test_analytics.py (~40 tests)
**Test Classes:**
- TestPortfolioMetrics - Overall portfolio performance
- TestCategoryPerformance - Performance by category
- TestTimeframePerformance - Performance by timeframe
- TestConfidenceDistribution - Distribution of confidence grades
- TestOptimalPortfolio - Portfolio recommendations
- TestPerformanceTrend - 90-day trend analysis
- TestEdgePerformance - Individual edge metrics
- TestRiskAnalysis - Risk assessment
- TestSampleQualityAnalysis - Sample quality metrics
- TestInstrumentAnalysis - Performance by instrument
- TestRobustnessScore - Portfolio robustness calculation

#### test_search_tradevault.py (~40 tests)
**Test Classes:**
- TestEdgeSearch - Search edges by title, category, performance
- TestPromptSearch - Search prompts
- TestInsightSearch - Search insights
- TestGlobalSearch - Cross-item search
- TestCategorySearch - Filter by category
- TestTimeframeSearch - Filter by timeframe
- TestConfidenceSearch - Filter by confidence grade
- TestPerformanceSearch - Filter by performance metrics
- TestTagSearch - Filter by tags
- TestSearchSuggestions - Autocomplete and suggestions
- TestSearchHistory - Save and retrieve search history

### Integration Tests

#### test_ui_backend_integration.py (~80 tests)
**Test Classes:**
- TestNoteWorkflow - Complete note lifecycle
- TestTaskWorkflow - Complete task lifecycle
- TestEdgeWorkflow - Complete edge lifecycle
- TestPromptWorkflow - Complete prompt lifecycle
- TestInsightWorkflow - Complete insight lifecycle
- TestCrossAppWorkflow - Multi-app scenarios

**Test Scenarios:**
- Create → Read → Update → Delete workflows
- Multi-step operations (create, search, modify, delete)
- Data persistence across operations
- User isolation and permissions
- Bulk operations
- Cross-app data aggregation
- Global search across apps

---

## Running Tests

### Using run_tests.py

```bash
# All tests
python run_tests.py all

# Unit tests only
python run_tests.py unit

# Integration tests only
python run_tests.py integration

# With coverage
python run_tests.py coverage

# Smoke tests (quick checks)
python run_tests.py smoke

# Specific test file
python run_tests.py specific unit/test_note_ops.py

# Tests for specific module
python run_tests.py module note_ops
```

### Using pytest Directly

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_note_ops.py -v

# Specific test class
pytest tests/unit/test_note_ops.py::TestNoteCreation -v

# Specific test function
pytest tests/unit/test_note_ops.py::TestNoteCreation::test_create_note_valid_data -v

# With coverage
pytest tests/ --cov=apps --cov=core --cov-report=html

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -s

# Run tests matching pattern
pytest tests/ -k "search" -v

# Mark-based filtering
pytest tests/ -m "unit" -v          # Only unit tests
pytest tests/ -m "database" -v      # Only tests using database
pytest tests/ -m "not slow" -v      # Skip slow tests
```

---

## Test Fixtures (conftest.py)

### Database Fixtures

```python
@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Session-scoped temporary database."""
    return os.path.join(tmp_path_factory.mktemp("db"), "test.db")

@pytest.fixture(autouse=True)
def fresh_db(test_db_path):
    """Fresh database for each test."""
    init_database(test_db_path)
    yield test_db_path
```

### User Fixtures

```python
@pytest.fixture
def test_user(test_db_path):
    """Create test user."""
    user_id = register_user('testuser', 'test@example.com', 'TestPassword123', test_db_path)
    return {'id': user_id, 'username': 'testuser', 'email': 'test@example.com'}

@pytest.fixture
def test_user2(test_db_path):
    """Create second test user for isolation testing."""
    user_id = register_user('testuser2', 'test2@example.com', 'TestPassword456', test_db_path)
    return {'id': user_id, 'username': 'testuser2', 'email': 'test2@example.com'}
```

### Sample Data Fixtures

```python
@pytest.fixture
def sample_note_data():
    """Sample note data for testing."""
    return {
        'title': 'Test Note',
        'content': 'This is test note content',
        'category': 'personal',
        'importance': 3
    }

@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        'title': 'Test Task',
        'description': 'This is test task description',
        'category': 'personal',
        'priority': 3
    }

# Similar fixtures for edges, prompts, insights, etc.
```

---

## Writing New Tests

### Test Structure

```python
import pytest
from apps.module.utils.feature import function_to_test
from core.exceptions import ValidationError

@pytest.mark.unit
@pytest.mark.database
class TestFeatureName:
    """Test feature_name operations."""

    def test_operation_valid_scenario(self, test_user, fixture_data, test_db_path):
        """Test operation with valid data."""
        result = function_to_test(test_user['id'], fixture_data, test_db_path)
        assert result is not None

    def test_operation_error_scenario(self, test_user, test_db_path):
        """Test operation with invalid data raises error."""
        with pytest.raises(ValidationError):
            function_to_test(test_user['id'], {}, test_db_path)
```

### Best Practices

1. **Use Fixtures** - Avoid duplicating test data setup
2. **Test Isolation** - Each test should be independent
3. **Clear Names** - Test names should describe what's being tested
4. **Arrange-Act-Assert** - Organize tests clearly
5. **One Assertion Per Test** - When possible, keep tests focused
6. **Error Handling** - Always test error paths

### Test Naming Convention

- `test_<operation>_<condition>` - e.g., `test_create_note_valid_data`
- `test_<operation>_<error_condition>_raises_error` - e.g., `test_create_note_missing_title_raises_error`

---

## Coverage Reports

### Generate Coverage Report

```bash
pytest tests/ --cov=apps --cov=core --cov-report=html --cov-report=term
```

### View Coverage Report

```bash
# HTML report opens in browser
start htmlcov/index.html          # Windows
open htmlcov/index.html           # macOS
xdg-open htmlcov/index.html       # Linux
```

### Coverage Goals

- Overall: >85% coverage
- Core modules: >95% coverage
- Business logic: >90% coverage
- Tests for edge cases and error paths

---

## CI/CD Integration

### GitHub Actions

Tests automatically run on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

Configuration: `.github/workflows/tests.yml`

**Matrix Testing:**
- Python 3.9, 3.10, 3.11
- Ubuntu, Windows, macOS

### Local Pre-commit Checks

```bash
# Run tests before committing
pre-commit run pytest --all-files
```

---

## Troubleshooting

### Database Locked Error

```bash
# Reset test database
rm -rf tests/tmp_*
```

### Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python run_tests.py all
```

### Fixture Not Found

```bash
# Verify conftest.py is in tests/ directory
# Ensure fixture names match exactly
```

### Tests Running Slowly

```bash
# Run only fast tests
pytest tests/ -m "not slow" -v

# Run specific module only
pytest tests/unit/test_note_ops.py -v
```

---

## Test Maintenance

### When Adding New Features

1. Write tests first (TDD)
2. Add test fixtures if needed
3. Update existing test classes if applicable
4. Run coverage report to verify coverage
5. Update this guide if needed

### When Modifying Features

1. Update related tests
2. Run tests to verify changes don't break functionality
3. Add new tests for new behavior
4. Verify coverage doesn't decrease

### Removing Features

1. Remove related tests
2. Update integration tests if applicable
3. Run full test suite to ensure no orphaned dependencies

---

## Performance Testing

### Identify Slow Tests

```bash
pytest tests/ --durations=10
```

### Profile Test Execution

```bash
pytest tests/ --profile
```

### Optimize Database Tests

- Use `fresh_db` fixture with autouse=True
- Batch database operations in tests
- Use temporary in-memory databases for unit tests

---

## Continuous Integration Status

Check test status and coverage:

- **GitHub Actions**: https://github.com/user/NoteTracker/actions
- **Coverage Badge**: ![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
- **Build Status**: [![Tests](https://github.com/user/NoteTracker/workflows/Tests/badge.svg)](https://github.com/user/NoteTracker/actions)

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest Fixtures Guide](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Python unittest/pytest Best Practices](https://realpython.com/pytest-python-testing/)
- [Testing Python Web Applications](https://testdriven.io/)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 600+ |
| **Unit Tests** | ~520 |
| **Integration Tests** | ~80 |
| **Test Files** | 12 |
| **Average Coverage** | >85% |
| **Pytest Fixtures** | 15+ |
| **Test Execution Time** | ~2-3 minutes |

**Phase 5: Comprehensive Testing is Complete and Ready for Execution!** 🎊

---

Created: 2026-01-12
Last Updated: 2026-01-12
