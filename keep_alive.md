# keep_alive.py

Simple Flask web server to keep the bot process alive on hosting platforms (e.g., Replit).

## Overview

Runs a minimal HTTP server on port 8080 in a background thread. Responds with `"I'm alive"` on the root endpoint, which external uptime monitors can ping.

## Functions

### `home()`

Flask route handler for `/`. Returns `"I'm alive"`.

### `keep_alive()`

Starts the Flask app in a daemon thread on `0.0.0.0:8080`. Werkzeug logging is suppressed to ERROR level.
