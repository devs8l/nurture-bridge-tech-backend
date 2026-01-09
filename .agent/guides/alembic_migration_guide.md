# Alembic Database Migration Guide

## What is Alembic?

Alembic is a database migration tool for SQLAlchemy. It helps you:
- Track database schema changes over time
- Apply changes to your database in a controlled way
- Rollback changes if needed
- Keep development, staging, and production databases in sync

## Initial Setup (One-Time)

Since you manually added the `doctor_notes` and `hod_notes` columns, we need to tell Alembic about the current state of your database.

### Step 1: Create a Baseline Migration

```bash
# Navigate to your project directory
cd "d:\Stellar\Nurture Bridge\nurture_bridge_backend"

# Create an initial migration that captures current database state
alembic revision --autogenerate -m "initial_baseline"
```

This will create a file like `alembic/versions/abc123_initial_baseline.py`.

### Step 2: Review the Generated Migration

Open the generated file and check if it's trying to create tables that already exist. If so, you have two options:

**Option A: Mark as applied without running (recommended for existing databases)**
```bash
# This tells Alembic "this migration is already applied"
alembic stamp head
```

**Option B: Edit the migration to be empty**
Edit the generated file and make both `upgrade()` and `downgrade()` functions empty:
```python
def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
```

Then run:
```bash
alembic upgrade head
```

---

## Daily Workflow: Making Database Changes

### Scenario 1: Adding a New Column

**Step 1: Update your SQLAlchemy model**

```python
# Example: Adding a new field to a model
class FinalReport(Base):
    # ... existing fields ...
    
    new_field: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Description of the field"
    )
```

**Step 2: Generate migration**

```bash
alembic revision --autogenerate -m "add_new_field_to_final_reports"
```

**Step 3: Review the generated migration**

Open `alembic/versions/xyz_add_new_field_to_final_reports.py` and verify it looks correct:

```python
def upgrade() -> None:
    op.add_column('final_reports', 
        sa.Column('new_field', sa.String(255), nullable=True),
        schema='report'
    )

def downgrade() -> None:
    op.drop_column('final_reports', 'new_field', schema='report')
```

**Step 4: Apply the migration**

```bash
alembic upgrade head
```

### Scenario 2: Adding a New Table

**Step 1: Create your SQLAlchemy model**

```python
class NewTable(Base):
    __tablename__ = "new_table"
    __table_args__ = {"schema": "report"}
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
```

**Step 2-4: Same as above** (autogenerate, review, upgrade)

### Scenario 3: Modifying an Existing Column

**Step 1: Update your model**

```python
# Change from String(100) to String(255)
name: Mapped[str] = mapped_column(String(255))  # was String(100)
```

**Step 2: Generate migration**

```bash
alembic revision --autogenerate -m "increase_name_field_length"
```

**Step 3: Review and potentially edit**

Sometimes Alembic doesn't detect column modifications. You may need to manually edit:

```python
def upgrade() -> None:
    op.alter_column('table_name', 'column_name',
                    type_=sa.String(255),
                    schema='report')

def downgrade() -> None:
    op.alter_column('table_name', 'column_name',
                    type_=sa.String(100),
                    schema='report')
```

**Step 4: Apply**

```bash
alembic upgrade head
```

---

## Common Alembic Commands

### Check Current Migration Status

```bash
# See which migrations are applied
alembic current

# See migration history
alembic history

# See pending migrations
alembic history --verbose
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply one migration forward
alembic upgrade +1

# Apply to a specific revision
alembic upgrade abc123
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade abc123

# Rollback all migrations
alembic downgrade base
```

### Create Manual Migration

```bash
# Create an empty migration file for manual edits
alembic revision -m "custom_migration_name"
```

---

## Best Practices

### ✅ DO:

1. **Always review auto-generated migrations** before applying
2. **Test migrations on a development database first**
3. **Use descriptive migration messages**: `add_user_email_index` not `update_db`
4. **Keep migrations small and focused**: One logical change per migration
5. **Add comments in complex migrations** to explain what and why
6. **Commit migrations to version control** along with model changes

### ❌ DON'T:

1. **Don't edit applied migrations** - Create a new migration instead
2. **Don't delete migrations** that have been applied to production
3. **Don't skip reviewing auto-generated migrations** - They can be wrong!
4. **Don't apply migrations directly to production** without testing

---

## Handling Data Migrations

Sometimes you need to migrate data, not just schema. Here's how:

```python
def upgrade() -> None:
    # First, add the new column
    op.add_column('users', sa.Column('full_name', sa.String(255)))
    
    # Then, migrate data
    connection = op.get_bind()
    connection.execute(
        """
        UPDATE users 
        SET full_name = first_name || ' ' || last_name
        WHERE full_name IS NULL
        """
    )
    
    # Finally, make it non-nullable if needed
    op.alter_column('users', 'full_name', nullable=False)

def downgrade() -> None:
    op.drop_column('users', 'full_name')
```

---

## Troubleshooting

### "Target database is not up to date"

```bash
# Check current version
alembic current

# Upgrade to latest
alembic upgrade head
```

### "Can't locate revision identified by 'xyz'"

The migration file might be missing. Check `alembic/versions/` directory.

### Migration fails midway

```bash
# Check what went wrong
alembic current

# If needed, manually fix the database and mark as applied
alembic stamp head
```

### Alembic detects changes you didn't make

This happens when your models don't match your database. Either:
1. Apply the changes if they're correct
2. Update your models to match the database
3. Edit the migration to remove unwanted changes

---

## Production Deployment Workflow

1. **Development**: Create and test migration locally
2. **Commit**: Add migration file to git
3. **Staging**: Deploy code and run `alembic upgrade head`
4. **Test**: Verify everything works in staging
5. **Production**: Deploy code and run `alembic upgrade head`

### Automated Deployment Script

```bash
#!/bin/bash
# deploy.sh

# Pull latest code
git pull

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Restart application
systemctl restart your-app
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Create migration | `alembic revision --autogenerate -m "description"` |
| Apply migrations | `alembic upgrade head` |
| Rollback one | `alembic downgrade -1` |
| Check status | `alembic current` |
| View history | `alembic history` |
| Mark as applied | `alembic stamp head` |

---

## Next Steps for Your Project

1. **Create baseline migration** (do this once):
   ```bash
   alembic revision --autogenerate -m "initial_baseline"
   alembic stamp head
   ```

2. **From now on**, whenever you change a model:
   ```bash
   alembic revision --autogenerate -m "describe_your_change"
   alembic upgrade head
   ```

3. **Before deploying to production**, always:
   - Test migration on development database
   - Backup production database
   - Run migration during low-traffic period
   - Have rollback plan ready

---

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
