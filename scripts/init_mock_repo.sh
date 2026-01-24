#!/bin/bash
# Initialize mock git repository with sample commit history
# This script should be run during project setup to create a test repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MOCK_REPO_DIR="$PROJECT_DIR/data/mock_repo"

echo "🔧 Initializing mock git repository at $MOCK_REPO_DIR"

# Navigate to mock repo directory
cd "$MOCK_REPO_DIR"

# Remove existing .git if present
if [ -d ".git" ]; then
    echo "   Removing existing .git directory..."
    rm -rf .git
fi

# Initialize git repository
echo "   Initializing git repository..."
git init -q

# Configure git user for this repo
git config user.email "dev@example.com"
git config user.name "Dev Team"

# Create commit history with multiple files and realistic timeline
echo "   Creating commit history..."

# Commit 1: Initial setup (Jan 18, 2026)
git add config.py
GIT_COMMITTER_DATE="2026-01-18T09:00:00Z" git commit -m "Initial config setup

- Add database configuration
- Set connection pool defaults" --date="2026-01-18T09:00:00Z" -q

# Commit 2: Add data models (Jan 19, 2026)
git add models.py
GIT_COMMITTER_DATE="2026-01-19T11:30:00Z" git commit -m "Add transaction and card models

- Create Transaction dataclass
- Create Card dataclass with validation
- Add expiry check method" --date="2026-01-19T11:30:00Z" -q

# Commit 3: Database connection pooling (Jan 20, 2026)
git add database.py
GIT_COMMITTER_DATE="2026-01-20T14:00:00Z" git commit -m "Implement database connection pooling

- Add PostgreSQL connection pool (max 10 connections)
- Implement retry logic
- Add connection timeout handling" --date="2026-01-20T14:00:00Z" -q

# Commit 4: Add API routes (Jan 21, 2026)
git add api_routes.py
GIT_COMMITTER_DATE="2026-01-21T10:15:00Z" git commit -m "Add payment API endpoints

- Implement /process-payment endpoint
- Implement /refund-transaction endpoint
- Wire up PaymentProcessor" --date="2026-01-21T10:15:00Z" -q

# Commit 5: RISKY - Payment processor changes (Jan 23, 2026 at 13:00 - 1.5 hours before incident!)
git add payment_processor.py
GIT_COMMITTER_DATE="2026-01-23T13:00:00Z" git commit -m "Refactor payment processing logic

BREAKING CHANGE: Simplified transaction validation
- Remove redundant null checks for performance
- Direct access to card.getExpiryDate() without validation
- Optimize database query timeout to 5s (was 30s)" --date="2026-01-23T13:00:00Z" -q

echo "✅ Mock repository initialized successfully!"
echo ""
echo "Commit history:"
git log --oneline --date=short --pretty=format:"   %h - %s (%ad)" --date=iso

echo ""
echo ""
echo "📊 Timeline correlation:"
echo "   13:00 - Risky commit deployed (removed null checks, reduced timeout)"
echo "   14:23 - Incident started (NullPointerException, Database timeouts)"
echo ""
