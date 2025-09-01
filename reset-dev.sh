#!/bin/bash
# reset-dev.sh

git checkout dev || exit 1
git fetch origin
git reset --hard origin/main
git push --force-with-lease origin dev