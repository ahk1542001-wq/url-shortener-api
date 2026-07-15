# Security Policy

## Supported Version

Security fixes are applied to the current `main` branch. This class project does not maintain older release branches.

## Reporting a Vulnerability

Please report security issues privately through GitHub's **Security** tab using a private vulnerability report. If private reporting is unavailable, contact the repository owner privately rather than opening a public issue.

Include:

- A clear description of the issue and impact.
- Reproduction steps or a minimal proof of concept.
- Affected endpoint, file, or deployment configuration.
- Any suggested mitigation.

Do not include production credentials, personal data, or destructive test results.

## Operational Security Notes

- Generate `JWT_SECRET` with `openssl rand -hex 32` or an equivalent cryptographically secure generator.
- Store `DATABASE_URL`, `ADMIN_PASSWORD_HASH`, and Cloudinary credentials only in environment variables.
- Rotate a credential immediately if it is exposed in chat, logs, screenshots, commits, or issue reports.
- Back up or branch the Neon database before applying migrations.
- Run destructive PostgreSQL tests only against a disposable database whose name contains `test`.
- Keep dependencies audited and apply supported security updates promptly.
