#!/bin/sh
# Write the dynamic flag from environment variable $FLAG into /flag.txt
echo "${FLAG:-NECROX{DEFAULT_LOCAL_FLAG}}" > /flag.txt

# Remove env var so users can't read it via /proc/self/environ (optional hard security measure)
unset FLAG

# Start the main challenge application
exec node server.js
