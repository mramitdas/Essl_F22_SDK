# Storage and Offline Mirror Implementation Plan

**Date:** 2026-10-24

**Spec:** `docs/superpowers/specs/2026-10-24-storage-mirror.md`

## Rules

- One issue = one branch = one PR = one logical change.
- Branch from updated `dev`; PR back to `dev`; merge before the next task.
- Every production change starts with a failing test.
- Do not push directly to `dev`, `stag`, or `prod`.
- Run all gates before opening the PR:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
```

## Task 1: Storage Contracts and Built-in Backends

**Files:**

- Create `src/essl_f22/storage/{__init__,base,codec,document,factory,jsonfile,memory,models,paths,sqlite}.py`
- Create `src/essl_f22/state.py`
- Create `tests/test_storage_codec.py`
- Create `tests/test_storage_contract.py`
- Create `tests/test_storage_factory.py`
- Create the storage spec and this plan

**Tests first:**

- Codec round trips for users, groups, timezones, user timezones, device info,
  and attendance.
- Attendance hash is stable and field-sensitive.
- Shared contract tests for memory, JSON, and SQLite:
  block state, mirror records, attendance upserts, sync state, clearing.
- JSON persistence, malformed files, and atomic replace failure.
- SQLite batch replace leaves no partial data.
- Platform default paths and factory selection.

**Implementation:**

- Define storage protocols and dataclasses.
- Implement JSON document codecs.
- Implement the shared `DocumentStorage` typed methods.
- Implement memory, atomic JSON, and transactional SQLite primitives.
- Add `create_storage()` and the `state.py` compatibility shim.

**Acceptance:**

- All built-ins pass the same contract tests.
- `SqliteBlockStateStore` and `default_state_path` are importable.
- Gates pass.

**Commit:** `feat: add storage contracts and built-in backends`

## Task 2: Offline Mirror and Sync

**Files:**

- Create `src/essl_f22/mirror.py`
- Create `tests/test_mirror.py`

**Tests first:**

- Read-only mirror accessors for users, groups, timezones, fingerprints,
  attendance filters, device info, and sync state.
- Full sync replaces all records.
- Incremental sync upserts attendance without duplicates.
- Incremental sync falls back to full attendance replacement when the device
  count drops.
- Sync result and sync state are persisted.
- Device serial mismatch is rejected.

**Implementation:**

- Add `DeviceLike` protocol and `Mirror`.
- Add `MirrorSnapshot`.
- Implement `Mirror.sync(device, mode)`.
- Add typed missing-record errors.

**Acceptance:**

- Fake-device tests cover full, incremental, and fallback paths.
- No device writes occur during sync.
- Gates pass.

**Commit:** `feat: add offline mirror synchronization`

## Task 3: Block Manager

**Files:**

- Create `src/essl_f22/access.py`
- Create `tests/test_access.py`

**Tests first:**

- Choose the highest free default-allow-all timezone.
- Do not reuse a slot referenced by groups or non-blocked users.
- Block, unblock, idempotence, and missing-state fallback.
- Verification failure restores the original assignment.
- No free slot raises `NoFreeTimeZoneSlotError`.

**Implementation:**

- Add `AccessDevice` protocol, `BlockResult`, `UnblockResult`, and
  `BlockManager`.
- Implement deny-all timezone creation and original-state persistence.

**Acceptance:**

- Block/unblock tests pass without hardware.
- No template or user deletion occurs.
- Gates pass.

**Commit:** `feat: add non-destructive access block manager`

## Task 4: Device Integration and Public API

**Files:**

- Modify `src/essl_f22/device.py`
- Modify `src/essl_f22/__init__.py`
- Delete `src/essl_f22/core.py`
- Delete `tests/test_core.py`
- Create `tests/test_public_api.py`
- Modify `tests/test_device.py`

**Tests first:**

- Storage injection wins over convenience selection.
- `storage_backend`, `storage_path`, and `storage_options` create a backend.
- Device block/unblock methods delegate correctly.
- `Device.mirror()` and `Device.sync()` use the configured storage.
- Public exports are importable; starter `add` API is gone.

**Implementation:**

- Add lazy storage selection to `Device`.
- Wire blocking, mirror, and sync methods.
- Export the public API.

**Acceptance:**

- All old tests still pass.
- No eager filesystem writes on `Device` construction.
- Gates pass.

**Commit:** `feat: wire storage and mirror into Device`

## Task 5: PostgreSQL and MySQL Adapters

**Files:**

- Create `src/essl_f22/storage/postgres.py`
- Create `src/essl_f22/storage/mysql.py`
- Create `tests/test_storage_sql_adapters.py`
- Modify `src/essl_f22/storage/factory.py`
- Modify `pyproject.toml`

**Tests first:**

- Factory selects adapters and reports missing drivers clearly.
- Integration tests run only when `ESSL_F22_POSTGRES_DSN` or
  `ESSL_F22_MYSQL_DSN` is set; otherwise skip.
- Integration tests run the shared contract.

**Implementation:**

- Add direct-driver document tables and transactional batch operations.
- Add optional extras `postgres` and `mysql`.
- Update the lockfile in a separate commit if required.

**Acceptance:**

- No top-level optional imports break the core.
- Integration tests pass when services are configured.
- Gates pass.

**Commit:** `feat: add PostgreSQL and MySQL storage adapters`

## Task 6: MongoDB and Redis Adapters

**Files:**

- Create `src/essl_f22/storage/mongo.py`
- Create `src/essl_f22/storage/redis.py`
- Create `tests/test_storage_nosql_adapters.py`
- Modify `src/essl_f22/storage/factory.py`
- Modify `pyproject.toml`

**Tests first:**

- Factory selects adapters and reports missing drivers clearly.
- Integration tests run only when `ESSL_F22_MONGO_URI` or
  `ESSL_F22_REDIS_URL` is set; otherwise skip.
- Integration tests run the shared contract.

**Implementation:**

- Add Mongo document collection/index handling.
- Add Redis hash-based namespace storage.
- Add optional extras `mongo` and `redis`.

**Acceptance:**

- No top-level optional imports break the core.
- Integration tests pass when services are configured.
- Gates pass.

**Commit:** `feat: add MongoDB and Redis storage adapters`

## Task 7: Documentation and Hardware Validation

**Files:**

- Modify `README.md`
- Modify `docs/index.md`
- Modify `AGENTS.md`
- Create `tests/test_hardware.py`
- Modify `pyproject.toml` if a hardware marker is needed

**Tests first:**

- Hardware tests are skipped unless `ESSL_F22_HOST` is set.
- Read-only mirror hardware test: connect, sync to memory storage, verify
  counts and a known user/fingerprint.
- No block/unblock hardware test runs by default.

**Implementation:**

- Document backend selection, mirror usage, sync modes, and credentials.
- Update the architecture section for `storage/` and `mirror.py`.
- Document that branch protection is unavailable on private free-plan repos;
  the branch-flow workflow and PR discipline are the enforcement mechanism.

**Acceptance:**

- Docs match the implemented API.
- Hardware tests are opt-in and read-only.
- Full gates pass.

**Commit:** `docs: document storage, mirror, and deployment`
