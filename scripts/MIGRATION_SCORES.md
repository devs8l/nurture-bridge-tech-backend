# Score Migration Instructions

## Problem
Existing completed assessment responses have `NULL` values for `total_score` and `max_possible_score`, causing pool summaries and final reports to have incorrect scores.

## Solution
Run the migration script to recalculate scores for all existing completed responses.

## Steps

### 1. Deploy the Score Calculation Fix
First, ensure the updated code is deployed:
```bash
git add app/api/v1/endpoints/assessment.py
git commit -m "Add score calculation logic to submit endpoint"
gcloud builds submit --tag gcr.io/nbt-backend/nurture-bridge-tech
gcloud run deploy nurture-bridge-tech --region asia-south1 --project nbt-backend --image gcr.io/nbt-backend/nurture-bridge-tech --platform managed
```

### 2. Run the Migration Script
```bash
# Activate your virtual environment
# Windows:
backend\Scripts\activate

# Run the migration
python scripts/migrate_recalculate_scores.py
```

### 3. Clean Up Old Reports
After scores are recalculated, delete existing summaries and reports:
```sql
-- Delete all pool summaries (they have wrong scores)
DELETE FROM report.pool_summaries;

-- Delete all final reports (they have wrong scores)
DELETE FROM report.final_reports;
```

### 4. Regenerate Reports
Call the `/generate-missing` endpoint for each child to regenerate reports with correct scores:
```bash
# Example for one child
curl -X POST "https://nurture-bridge-tech-862338790942.asia-south1.run.app/api/v1/reports/child/{child_id}/generate-missing" \
  -H "Authorization: Bearer {token}"
```

Or create a script to regenerate for all children.

## What the Migration Does

1. Finds all COMPLETED responses with NULL scores
2. For each response:
   - Sums all answer scores → `total_score`
   - Calculates max possible from question age protocols → `max_possible_score`
   - Updates the response record
3. Commits in batches of 10 for efficiency
4. Logs progress and results

## Expected Output
```
Starting score migration...
Found 25 completed responses with NULL scores
[1/25] Updated response abc-123: score=15/32
[2/25] Updated response def-456: score=22/28
...
Committed batch (total: 10)
...
============================================================
Migration Complete!
  Total responses: 25
  Updated: 25
  Failed: 0
============================================================
```

## Verification
After migration, check that scores are populated:
```sql
SELECT id, total_score, max_possible_score, status
FROM assessment.responses
WHERE status = 'COMPLETED'
LIMIT 10;
```

All completed responses should now have non-NULL scores.
