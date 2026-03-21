# SECURITY_POLICY.md — Structured Mode v2

Security is a design constraint, not a feature.

This document defines baseline security discipline for this project.

All contributors and AI agents must follow this policy.

---

# 1. Security Principles

1. Minimize attack surface.
2. Validate all inputs at boundaries.
3. Trust no external input.
4. Least privilege by default.
5. Avoid unnecessary exposure.
6. Prefer secure defaults.
7. Fail safely.

Security must not be sacrificed for convenience.

---

# 2. Input Validation Rules

All inputs must be validated at the boundary layer:

- API endpoints
- CLI commands
- IPC channels
- File imports
- External integrations

Validation must include:

- Type validation
- Range validation
- Format validation
- Required field validation

Never rely solely on interface-layer validation.

Domain logic must assume inputs may be malicious or malformed.

---

# 3. Authentication & Authorization (If Applicable)

If authentication exists:

- Passwords must never be stored in plaintext.
- Use salted hashing.
- Do not log sensitive credentials.
- Do not expose user identifiers unnecessarily.

If authorization exists:

- Enforce role checks in application layer.
- Do not rely on UI-based restrictions.
- Validate permissions at use-case boundary.

---

# 4. Secrets Handling

Secrets include:

- API keys
- Encryption keys
- Tokens
- Credentials
- Private certificates

Rules:

- Never commit secrets to repository.
- Use environment variables or secure stores.
- Do not log secrets.
- Do not expose secrets to interface layer.
- Do not store secrets in client-visible code.

`.gitignore` must exclude secret files.

---

# 5. Dependency Hygiene

Before adding a dependency:

- Evaluate necessity.
- Avoid heavy frameworks casually.
- Avoid abandoned packages.
- Avoid packages with known vulnerabilities.
- Prefer well-maintained libraries.

When updating dependencies:

- Check for breaking changes.
- Review security advisories.

Do not add dependencies without justification.

---

# 6. Logging Discipline

Logs must:

- Avoid printing sensitive data.
- Avoid printing full payloads containing secrets.
- Avoid leaking internal paths unnecessarily.
- Avoid exposing stack traces in production builds.

Debug logging must be disabled in production builds.

---

# 7. Data Protection

If persistence exists:

- Validate file paths.
- Avoid arbitrary file access.
- Prevent directory traversal.
- Validate file import formats.
- Validate file sizes before processing.

If encryption is used:

- Use established cryptographic libraries.
- Do not implement custom crypto.
- Use modern, secure algorithms.
- Manage key lifecycle intentionally.

---

# 8. Public Contract Protection

Public interfaces must:

- Expose minimal necessary fields.
- Avoid exposing internal IDs unnecessarily.
- Avoid leaking implementation details.
- Avoid exposing debug or internal endpoints.

Breaking changes to contracts require:

- ADR
- Version bump
- Documentation update

---

# 9. Error Handling Rules

Errors must:

- Avoid leaking internal implementation details.
- Avoid exposing stack traces in production.
- Return user-safe messages.
- Log sensitive errors internally only.

Fail securely — not silently.

---

# 10. Local-First Application Rules (If Applicable)

If project stores local user data:

- Do not assume trusted environment.
- Validate database integrity.
- Avoid silent corruption.
- Consider optional encryption at rest.
- Protect backups.

If packaging exists:

- Ensure packaged build does not expose debug tooling.
- Ensure production build disables dev-only features.

---

# 11. Refactor Security Rules

Refactor milestones must:

- Preserve existing security constraints.
- Not remove validation.
- Not widen attack surface.
- Not bypass authorization checks.
- Not introduce cross-layer leaks.

If refactor affects boundary validation:
- Re-test security behavior manually.

---

# 12. Migration Security Rules

When performing migrations:

- Validate transformation logic.
- Avoid silent data truncation.
- Avoid lossy transformations.
- Back up data before breaking changes.
- Validate row counts before/after migration.

---

# 13. AI Guardrails — Security

AI must:

- Not introduce unsafe input handling.
- Not add insecure random number generation for security features.
- Not disable validation for convenience.
- Not remove authentication checks.
- Not expose secrets in logs.
- Not weaken cryptographic configuration.

If uncertain about security implications, ask before implementing.

---

# 14. Security Testing (Manual)

Before release:

- [ ] Attempt invalid input injection.
- [ ] Attempt malformed file import.
- [ ] Verify input validation boundaries.
- [ ] Verify error messages do not leak sensitive info.
- [ ] Verify secrets are not logged.
- [ ] Verify production mode disables debug tools.

Document findings in RUNTIME_VERIFICATION_REPORT.md.

---

# 15. Vulnerability Response Policy

If a security issue is discovered:

1. Do not publicly disclose immediately.
2. Fix issue in a patch branch.
3. Release PATCH version.
4. Document in CHANGELOG under Security.
5. If severe, consider MAJOR release with migration guidance.

Security fixes must not bundle unrelated features.

---

# 16. Guiding Rule

Security failures damage trust.

Structure protects maintainability.  
Security protects users.  

Security discipline must never erode silently.
