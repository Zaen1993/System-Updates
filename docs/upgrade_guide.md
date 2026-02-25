# Upgrade Guide

## Version 16.x to 16.y

### Server
1. Backup current database and configuration.
2. Pull latest changes from repository.
3. Install new dependencies: `pip install -r server/requirements.txt`
4. Run database migrations if any.
5. Restart server.

### Android Client
1. Update `base_url` in `Communicator.kt` if changed.
2. Rebuild APK: `./gradlew assembleRelease`
3. Distribute new APK to devices.
4. Devices will auto-update via Dead Drops if configured.

## Database Migrations

### Adding new tables
Execute the SQL files in `database/` in order.

### Modifying existing tables
Create migration scripts and document changes.

## Configuration Changes

### New environment variables
Check `.env.example` for new variables and add them to your environment.

### Deprecated variables
Remove any deprecated variables after confirming they are no longer needed.

## Rollback Procedure
1. Restore database from backup.
2. Revert code to previous version.
3. Restart server.
4. Reinstall previous APK on devices if necessary.

## Testing
Always test upgrades in a staging environment first.