# exceptions.py

Logging configuration for the bot.

## Overview

Sets up a module-level logger named `"MediaBiasBot"` with `INFO` level and timestamped format.

## Exports

- `logger` — the shared logger instance used across all modules.
- `print_exception()` — logs the current exception with traceback via `logger.exception()`.
