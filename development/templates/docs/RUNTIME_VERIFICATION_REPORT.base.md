# RUNTIME_VERIFICATION_REPORT.md — Structured Mode v2

This document records manual runtime verification evidence.

It must be completed:

- Before marking a milestone complete.
- Before cutting a release.
- After refactor milestones.
- After migration changes.
- After packaging/distribution changes (if applicable).

Do not skip verification.

---

# 1. Verification Metadata

Project Version:
Date:
Verifier:
Active Milestone:

Environment:

- OS:
- Runtime:
- Database Version (if applicable):
- Build Mode: (dev / prod / packaged)
- Commit Hash (if applicable):

---

# 2. Build Verification

Command Used:

    <build command>

Result:

- [ ] Build succeeded
- [ ] No warnings requiring action
- [ ] No unexpected output

Notes:

---

# 3. Test Verification

Command Used:

    <test command>

Result:

- [ ] All tests passed
- [ ] No skipped tests without justification
- [ ] No flaky failures

Notes:

---

# 4. Application Startup Verification

Command Used:

    <run command>

Result:

- [ ] Application launches successfully
- [ ] No runtime crashes
- [ ] No unhandled promise exceptions
- [ ] No console errors
- [ ] No missing resource errors

Notes:

---

# 5. Core Workflow Verification

Verify primary workflows for current milestone.

Checklist:

- [ ] Create entity
- [ ] Update entity
- [ ] Delete entity
- [ ] Persist data across restart
- [ ] Reload and verify integrity
- [ ] Validate input constraints
- [ ] Validate error handling

Add milestone-specific workflow checks below:

- [ ]
- [ ]
- [ ]

Notes:

---

# 6. Persistence Verification (If Applicable)

- [ ] Schema version matches expected
- [ ] Migrations applied successfully
- [ ] No data corruption
- [ ] No silent truncation
- [ ] Data preserved across restart

If migration was applied:

- [ ] Backup created
- [ ] Upgrade validated
- [ ] Previous version upgrade path tested

Notes:

---

# 7. Public Contract Verification

Verify no unintended public contract changes.

- [ ] API endpoints unchanged (unless expected)
- [ ] DTO structures unchanged (unless versioned)
- [ ] CLI commands unchanged (unless expected)
- [ ] Configuration file formats unchanged
- [ ] IPC channels unchanged (if applicable)

If changes occurred:

- [ ] ADR created
- [ ] Version bumped appropriately
- [ ] CHANGELOG updated

Notes:

---

# 8. Refactor Parity Verification (If Refactor Milestone)

- [ ] Behavior matches previous version
- [ ] No public contract drift
- [ ] No persistence change
- [ ] No performance regression observed
- [ ] No cross-layer boundary violations introduced

Manual regression test summary:

---

# 9. Determinism Verification (If Applicable)

If project requires deterministic behavior:

- [ ] Identical inputs produce identical outputs
- [ ] No floating-point drift
- [ ] No non-deterministic ordering issues
- [ ] Stable output across multiple runs

Test inputs used:

---

# 10. Performance Sanity Check (Optional)

- [ ] No obvious regressions
- [ ] Startup time acceptable
- [ ] Core workflow latency acceptable

Notes:

---

# 11. Security Baseline Check

- [ ] Input validation enforced
- [ ] No sensitive data exposed in logs
- [ ] No debug endpoints left enabled
- [ ] Secure runtime defaults preserved

Notes:

---

# 12. Packaging Verification (If Applicable)

If packaged build:

- [ ] Installer/build artifact created
- [ ] Application installs successfully
- [ ] Application launches in packaged mode
- [ ] No missing resources
- [ ] Persistence works in packaged environment
- [ ] Uninstall/reinstall tested (if applicable)

Notes:

---

# 13. Final Sign-Off

I confirm that:

- All Definition of Done requirements are met.
- All milestone completion criteria are satisfied.
- No undocumented architectural changes were introduced.
- Versioning rules were followed.

Verifier Signature:
Date:

---

# Guiding Rule

Manual verification replaces CI in Structured Mode.

Do not mark milestones complete without this report.
