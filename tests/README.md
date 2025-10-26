# Networth Tracker Test Suite

## Running Backend Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_models.py

# Run with coverage
python -m pytest --cov=src tests/

# Run with unittest (alternative)
python -m unittest discover tests/
```

## Running Frontend Tests

```bash
# Install Jest (if not installed)
npm install --save-dev jest

# Run JavaScript tests
npm test

# Run with coverage
npm test -- --coverage
```

## Test Structure

### Backend Tests (`tests/`)
- `test_models.py` - Model unit tests
- `test_services.py` - Service layer tests
- `test_database.py` - Integration tests

### Frontend Tests (`static/js/tests/`)
- `test.spec.js` - JavaScript functionality tests

## Test Coverage Goals
- Models: >90%
- Services: >85%
- Controllers: >80%
- Integration: Key workflows covered
