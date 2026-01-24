# Mock Data Timeline Correlation

## Incident Timeline: January 23, 2026

### Git Commits
```
c75c536 - 2026-01-18 09:00:00 - Initial config setup
568f232 - 2026-01-19 11:30:00 - Add transaction and card models
513a87d - 2026-01-20 14:00:00 - Implement database connection pooling
3466c3b - 2026-01-21 10:15:00 - Add payment API endpoints
1d67663 - 2026-01-23 13:00:00 - ⚠️  RISKY: Refactor payment processing logic
```

**Problematic Commit (1d67663):**
- Removed null checks for "performance optimization"
- Direct access to `card.getExpiryDate()` without validation
- Reduced database timeout from 30s to 5s
- Deployed at 13:00, incident started at 14:23 (1h 23min later)

### Service Logs Timeline

#### Payment Service (payment-service.log)
- `13:45` - Service started normally
- `14:15` - Normal payment processing
- `14:23:45` - **First ERROR**: Database timeout
- `14:23:45` - **NullPointerException** in payment_processor.py line 42
- `14:23:50` - **CRITICAL**: Database pool exhausted (0/10 connections)
- `14:24:05` - Circuit breaker activated
- `14:25:00` - Manual intervention, service recovered

#### Database Service (database-service.log)
- `14:22:30` - WARNING: Connection pool 85% utilized
- `14:22:45` - WARNING: Connection pool 92% utilized
- `14:23:00` - **CRITICAL**: Max connections (100) reached
- `14:23:30` - Query timeout (32000ms)
- `14:23:45` - Deadlock detected
- `14:25:30` - System stable again

#### Auth Service (auth-service.log)
- `14:20:00` - Slow queries detected (450-520ms)
- `14:21:30` - Redis connection lost
- `14:22:00` - High database latency (850ms avg)
- `14:23:00` - Service recovered

## Root Cause Analysis

The agent should correlate:

1. **Code Change**: Commit `1d67663` at 13:00
   - Removed null checks → NullPointerException
   - Reduced timeout 30s→5s → Database timeouts
   
2. **Incident Start**: 14:23 (83 minutes after deployment)
   - First errors: Database timeout + NullPointerException
   - Cascading failure: Connection pool exhaustion
   
3. **Evidence Trail**:
   - Stack trace shows line 42 in payment_processor.py (the modified file)
   - Error: `Transaction.getCard().getExpiryDate()` with null card
   - Database timeouts align with reduced timeout setting

## Expected Agent Findings

The incident responder should identify:
- **Culprit Commit**: `1d67663`
- **Root Cause**: Removed null validation + aggressive timeout
- **Timeline Match**: Commit 1.5h before incident
- **Recommendation**: Revert commit, restore null checks and 30s timeout
