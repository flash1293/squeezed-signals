# Copilot Instructions for squeezed-signals

## Python Environment

This project uses a Python virtual environment located in `.venv/` at the project root.

**To run Python commands:**
- Use: `/Users/joereuter/Clones/squeezed-signals/.venv/bin/python`
- Instead of: `python` or `python3`

**Example:**
```bash
# DON'T use:
python3 script.py

# DO use:
/Users/joereuter/Clones/squeezed-signals/.venv/bin/python script.py
```

## Project Structure

The project has three main directories:
- `logs/` - Log compression experiments
- `metrics/` - Metrics/time-series compression experiments
- `traces/` - Distributed tracing compression experiments

Each directory contains numbered phase scripts (e.g., `00_generate_data.py`, `01_storage.py`, etc.) that demonstrate progressive compression techniques.

## Dependencies

All Python dependencies are listed in `requirements.txt` and should already be installed in the `.venv` environment.
