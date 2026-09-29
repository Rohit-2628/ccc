#!/bin/sh
# Dynamic flag injection
echo "${FLAG:-FLAG{placeholder_flag}}" > /flag.txt
unset FLAG
exec node server.js
