#!/bin/bash
set -e
alembic upgrade head
python seed.py
exec "$@"
