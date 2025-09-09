# Pre-Implementation Checklist

Before implementing ANY feature, confirm:

## Current State Check
- [ ] Run `npm run check` - are there any errors?
- [ ] Run `npm run check:size` - note files already over 250 lines
- [ ] DO NOT modify any file already over 250 lines without refactoring first

## Quality Guidelines for All New Code
- [ ] New service files must be < 200 lines
- [ ] New component files must be < 150 lines
- [ ] New route files must be < 100 lines
- [ ] New model files must be < 100 lines
- [ ] Functions must be < 30 lines each
- [ ] API service files must be < 50 lines

## For Snapshot Feature Specifically
Create NEW files only, don't add to existing large files:

### Backend Files (Total: < 500 lines)
- [ ] `backend/app/models/snapshot.py` (< 100 lines)
- [ ] `backend/app/services/snapshot_service.py` (< 200 lines)  
- [ ] `backend/app/api/v1/endpoints/snapshots.py` (< 100 lines)
- [ ] `backend/alembic/versions/xxx_add_snapshots.py` (migration)

### Frontend Files (Total: < 400 lines)
- [ ] `frontend/src/components/SnapshotButton.tsx` (< 100 lines)
- [ ] `frontend/src/components/SnapshotTimeline.tsx` (< 150 lines)
- [ ] `frontend/src/services/snapshotApi.ts` (< 50 lines)
- [ ] `frontend/src/types/snapshot.ts` (< 50 lines)

## Implementation Rules
- [ ] NEVER modify App.tsx (already 4,494 lines)
- [ ] NEVER add to files already over 300 lines
- [ ] Break functions into smaller pieces if they exceed 30 lines
- [ ] Extract reusable logic into separate utility files
- [ ] Use TypeScript interfaces for all data structures

## Post-Implementation Verification
- [ ] Run `npm run check` - must pass with no errors
- [ ] Run `npm run type-check` - must pass with no errors
- [ ] Test on mobile (375px width) - must be responsive
- [ ] Verify snapshot creation works end-to-end
- [ ] Verify timeline visualization displays correctly
- [ ] Check database migrations apply successfully

## Success Criteria
✅ All new files under their size limits
✅ No existing files modified beyond limits
✅ Snapshot feature fully functional
✅ Mobile responsive design
✅ All quality checks pass
✅ Database properly migrated

## Emergency Brakes
🚨 **STOP IMMEDIATELY** if:
- Any file exceeds its limit during development
- Quality check script returns errors
- TypeScript compilation fails
- Database migration fails

## Development Process
1. **Plan First**: Review this checklist completely
2. **Check Current**: Run quality checks to understand baseline
3. **Create Structure**: Start with models, then services, then routes, then UI
4. **Test Incrementally**: Verify each piece works before moving to next
5. **Final Verification**: Run all checks before considering complete

Remember: **Quality over speed**. It's better to have clean, maintainable code than to rush and create technical debt.