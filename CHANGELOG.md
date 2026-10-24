# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Complete layperson-friendly handbook with concepts, guides, reference, help,
  and contributing pages, plus a strict MkDocs build in CI.
- Expanded README with requirements, installation, quickstart, common tasks,
  storage, safety, compatibility, error handling, and development guidance.

## [0.1.0] - 2026-10-24

### Added

- Synchronous TCP SDK for eSSL/ZKTeco F22 terminals.
- Device information, user, fingerprint metadata, attendance, group, and
  timezone reads.
- User create, update, and delete APIs.
- Non-destructive user blocking and unblocking.
- Read-only offline mirror with full and incremental sync.
- SQLite, JSON, memory, PostgreSQL, MySQL, MongoDB, and Redis storage backends.
- Optional dependency extras for external storage drivers.
- Hardware, storage-contract, and unit test suites.
- PyPI packaging with Trusted Publishing.
