# CI Pipeline for wpa

This directory contains the CI pipeline configuration for the Claude Code Orchestrator.

## Commands

- **Tests**: `pytest --cov=. tests/`
- **Lint**: `ruff check .`
- **Security**: `bandit -r . && safety check`

## Metrics

The pipeline tracks these metrics:
{
  "performance": {
    "response_time": {
      "target": -5,
      "cap": 10,
      "unit": "%"
    },
    "throughput": {
      "target": 5,
      "cap": -10,
      "unit": "%"
    },
    "memory_usage": {
      "target": 0,
      "cap": 15,
      "unit": "%"
    }
  }
}

## Usage

Run the full pipeline:
```bash
python ci/pipeline.py
```

Or use with orchestrator:
```bash
orchestrator "Add new feature X"
```
