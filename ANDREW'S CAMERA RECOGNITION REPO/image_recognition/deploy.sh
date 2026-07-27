#!/usr/bin/env bash
# deploy.sh — push only the necessary files to the Pi (skips venv/dataset/etc.)
# Run from the Mac:  ./deploy.sh
set -e

cd "$(dirname "$0")"   # the image_recognition folder

rsync -av \
  --exclude='.venv' \
  --exclude='dataset' \
  --exclude='runs' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  --exclude='yolo11n.pt' \
  --exclude='.DS_Store' \
  ./ firestingray:~/tokyo_robotics/image_recognition/

echo "Deploy complete."
