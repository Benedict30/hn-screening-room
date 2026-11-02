#!/bin/sh
# Run HN Screening Room at http://localhost:8765
cd "$(dirname "$0")"
(sleep 1; xdg-open "http://localhost:8765" 2>/dev/null || open "http://localhost:8765") &
python3 -m http.server 8765
