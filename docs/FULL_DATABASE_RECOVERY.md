# Full Supabase logical recovery preparation

The existing daily application snapshot is already verified. The separate manual
workflow full-database-recovery.yml additionally dumps logical roles, schema and
data, including auth.users and auth.identities. It follows the
[Supabase backup/restore procedure](https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore)
and its [CI restore check](https://supabase.com/docs/guides/deployment/ci/backups).
The CLI is pinned to v3.0.0, verified from the official release feed during setup.

## Private credential setup

The repository variable RAGEVAL_DATABASE_HOST is configured from this project's
Connect → Session pooler panel. Add **RAGEVAL_DATABASE_PASSWORD** as an encrypted
GitHub Actions secret, using the existing Supabase database password. Enter only
the password in GitHub's Secret field; do not put it in chat, a command, or a
repository file. The script safely encodes special characters when building the
session-pooler URI. The REST API/server key cannot replace this database password.
No change to the live database password is required.

## What the manual workflow does

1. Dumps roles, schema and COPY-formatted data to a private runner directory.
2. Requires explicit COPY sections for both RAGeval tables and Auth users/identities.
3. Starts a disposable local Supabase Postgres instance on the runner.
4. Loads roles/schema/data in one transaction with stop-on-error.
5. Compares restored table counts against the data dump's COPY records.
6. Encrypts the backup package and verifies its authenticated decryption.
7. Uploads ciphertext/HMAC/checksum only, retained for seven days.
8. Stops the disposable database. Failures open a repository issue.

The live project is a read-only dump source and is never used as a restore target.
This workflow stays manual until its first credentialed execution passes. Do not
claim it passed based on mocked tests or the application-only restore report.

## Recovery boundaries

Database data includes Auth password hashes and identities. Protect the encrypted
archive and the separate backup key. Restore into a compatible Supabase instance,
then configure application URLs, SMTP, provider credentials and secrets separately.
Storage file bytes, Edge Function deployments, Vault root encryption keys and
platform configuration are separate recovery tasks; a SQL backup does not include
all of those. The procedure excludes Supabase vector-storage metadata tables as
specified by the official guide. No claim of platform-wide disaster recovery is
made by restoring only database contents.

## Missing confirmation email

Custom SMTP is currently disabled. Supabase's built-in sender restricts recipients
to organization members and applies a small shared quota. See the
[SMTP guide](https://supabase.com/docs/guides/auth/auth-smtp) and
[error codes](https://supabase.com/docs/guides/auth/debugging/error-codes).
The app now distinguishes a restricted recipient from a provider email limit and
provides a Resend confirmation button. Recover/resend still avoid revealing
whether an address is registered. A general public launch needs a configured SMTP
provider and a verified sender; that has not been provisioned by these changes.
