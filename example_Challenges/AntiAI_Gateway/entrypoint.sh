#!/bin/sh
# Write the dynamic flag from environment variable $FLAG into /flag.txt
echo "${FLAG:-CYBERANZEN{4NT1_41_PR0P4G4ND4_HUM4N5_R3M41N_SUPR3M3}}" > /flag.txt

# Remove env var so users can't read it via /proc/self/environ (hard security measure)
unset FLAG

# Start the main challenge application
exec node server.js
