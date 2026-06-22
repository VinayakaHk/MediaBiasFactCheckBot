#!/bin/bash
# Run the full test suite. No hardcoded filenames — pytest autodiscovers test_*.py in tests/
exec uv run pytest tests/ -v "$@"
