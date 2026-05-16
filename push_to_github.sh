#!/usr/bin/env bash
#
# Push CCRTS project to your GitHub repository.
# Usage: bash push_to_github.sh
#
# Repository: https://github.com/shaiksalmabanu595-dot/AFDE_MAY6_Salma_CCRTS
#

set -e

REPO_URL="https://github.com/shaiksalmabanu595-dot/AFDE_MAY6_Salma_CCRTS.git"

echo "==> Initializing git repository"
git init -b main

echo "==> Configuring git user (edit these to your real name/email if not yet set globally)"
# Uncomment and edit if needed:
# git config user.name "Salma"
# git config user.email "your-email@example.com"

echo "==> Adding remote"
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

echo "==> Day 1 commit: Backend + DB schema"
git add backend/ database/ requirements.txt .gitignore
git commit -m "Day 1: Backend API, database schema, and project structure" || true

echo "==> Day 2 commit: Frontend"
git add frontend/
git commit -m "Day 2: React frontend with authentication and complaint management UI" || true

echo "==> Day 3 commit: Documentation + screenshots"
git add README.md docs/ screenshots/
git commit -m "Day 3: README, API docs, design docs, and screenshots placeholder" || true

echo "==> Pushing to GitHub (you'll be asked for your username + Personal Access Token)"
git push -u origin main

echo ""
echo "==> Done! Visit https://github.com/shaiksalmabanu595-dot/AFDE_MAY6_Salma_CCRTS"
echo "==> Remember to make the repo PUBLIC in repo Settings > General > Danger Zone > Change visibility"
