# Security Policy

## Supported version

Security fixes are applied to the latest `main` branch.

## Reporting a vulnerability

Please do not disclose vulnerabilities, employee data, bot tokens, database URLs, or Telegram IDs in a public issue.

Report security problems privately through GitHub Security Advisories when available, or contact the repository owner through a private channel. Include reproduction steps and impact, but do not attach a production database or real employee records.

## Secret handling

- Keep `.env` outside Git.
- Store deployment secrets with file mode `0600` or in a secrets manager.
- If a token is ever committed, revoke it immediately through `@BotFather`; deleting it in a later commit is not sufficient.
- Treat databases, backups, CSV imports, logs, and exported messages as personal data.

## Telegram privacy

The bot intentionally accepts commands only in private chats from explicitly allowlisted users. Disable group invitations through `@BotFather` with `/setjoingroups` and periodically review `ALLOWED_USERS` and `NOTIFY_CHAT_IDS`.
