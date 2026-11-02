#!/bin/bash
# Double-click on a Mac to run HN Screening Room at http://localhost:8765
cd "$(dirname "$0")"
(sleep 1; open "http://localhost:8765") &
python3 -m http.server 8765
