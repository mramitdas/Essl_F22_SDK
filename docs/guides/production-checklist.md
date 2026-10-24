# Production checklist

## Why this matters

A successful test on a lab device proves that the protocol works. It does not
prove that the integration is safe for real people, real attendance, and real
access decisions. This checklist closes the operational gaps: ownership,
network exposure, backups, verification, monitoring, privacy, and recovery.

Use it before the first production run and again after any material change.

## 1. Ownership and approval

- [ ] A named owner is responsible for the device and the integration.
- [ ] A named owner is responsible for access-control policy.
- [ ] The change has written approval.
- [ ] The maintenance window and rollback window are agreed.
- [ ] Someone can physically access the device if the network fails.
- [ ] The incident contact list is current.

## 2. Network and exposure

- [ ] The device is on a dedicated VLAN or trusted network segment.
- [ ] Only approved hosts can reach TCP port `4370`.
- [ ] Port `4370` is **not** exposed to the public internet.
- [ ] Firewall rules are documented and reviewed.
- [ ] VPN or jump-host access is required for remote administration.
- [ ] The device IP is static or reserved by DHCP.
- [ ] The host running the SDK has a stable address or documented NAT path.
- [ ] Network latency and packet loss have been measured during peak hours.
- [ ] The device's TCP port and communication key are recorded in the
  configuration inventory.

## 3. Credentials and secrets

- [ ] The communication key is stored in a secret store, not source code.
- [ ] Database passwords and DSNs are stored in a secret store.
- [ ] Secrets are not printed in logs, exception messages, or tickets.
- [ ] Credentials are rotated on a defined schedule.
- [ ] The database user has least privilege.
- [ ] TLS is enabled for database connections that cross untrusted networks.
- [ ] The communication key is not treated as strong authentication for the
  device network.

## 4. Device baseline

- [ ] Model, platform, firmware, and serial are recorded.
- [ ] User, fingerprint, attendance, group, and timezone counts are recorded.
- [ ] A sample user is compared with the device display or vendor software.
- [ ] A sample attendance record is compared with the device display.
- [ ] Timezone slots and group assignments are understood.
- [ ] The device clock is correct for its timezone.
- [ ] Daylight-saving behaviour is understood.
- [ ] The device's capacity limits are known.
- [ ] A read-only sync has completed and its counts match expectations.

```bash
# Reachability check examples
nc -vz DEVICE_IP 4370
# or on Windows PowerShell
Test-NetConnection -ComputerName DEVICE_IP -Port 4370
```

## 5. Read-only proof

- [ ] The first production run uses only read methods.
- [ ] No `set_*`, `delete_*`, `block_*`, or `unblock_*` call is reachable in the
  read-only path.
- [ ] The read path has a timeout and a bounded retry policy.
- [ ] The mirror path is tested.
- [ ] The read path does not print fingerprint templates.
- [ ] The read path does not log full personal records unnecessarily.

## 6. Backup and state

- [ ] The mirror path is explicit and on durable storage.
- [ ] The block-state path is explicit and backed up separately if needed.
- [ ] A restore of the storage backup has been tested.
- [ ] The backup is encrypted and access-controlled; it contains user password
  fields and personal data.
- [ ] The backup contains no communication key or database credentials.
- [ ] The retention period is defined.
- [ ] Old snapshots are deleted securely.
- [ ] The team knows that the mirror cannot restore fingerprint templates.
- [ ] A vendor-supported device backup/restore process exists if biometric
  recovery is required.

## 7. Access changes

- [ ] Blocking and unblocking have been tested on a non-production user.
- [ ] The state store is backed up before a block.
- [ ] A free default-allow-all timezone slot was confirmed.
- [ ] The user's original assignment was recorded outside the state store.
- [ ] Access was tested at the door, not only through the API.
- [ ] The team knows that `unblock_user()` with no saved state disables personal
  scheduling.
- [ ] The team knows that deleting a user and blocking a user are different.
- [ ] A lost-state recovery procedure is documented.

## 8. Write safety

- [ ] Every update reads the existing record first.
- [ ] Every write preserves fields that are not intentionally changed.
- [ ] UID ranges and encoded field lengths are validated before writing.
- [ ] Deletes have a backup and a second-person review.
- [ ] Batch jobs stop on the first unexpected result.
- [ ] Batch jobs have a resume plan.
- [ ] Writes are verified with a read-back.
- [ ] Ambiguous timeouts are investigated before retrying.
- [ ] Writes are logged with operator, target, and result.

## 9. Scheduling and performance

- [ ] Sync frequency is defined.
- [ ] Full and incremental sync schedules are documented.
- [ ] Sync runs off-peak where possible.
- [ ] Only one sync per device serial runs at a time.
- [ ] Timeout values are appropriate for the attendance volume.
- [ ] Memory use for large attendance reads is measured.
- [ ] Storage growth is monitored.
- [ ] Database connection limits are respected.
- [ ] JSON is not used for high-volume concurrent writes.
- [ ] Redis durability and eviction policy are confirmed, if used.

## 10. Monitoring and alerting

- [ ] Connection failures are alerted.
- [ ] Authentication failures are alerted.
- [ ] Sync failures are alerted.
- [ ] An unexpected `attendance_replaced=True` is alerted.
- [ ] A large drop in device or mirror counts is alerted.
- [ ] Disk and database capacity are monitored.
- [ ] The device's own event log or tamper alerts are monitored separately.
- [ ] Logs exclude secrets and biometric templates.
- [ ] A runbook links to [Troubleshooting](../help/troubleshooting.md).

## 11. Privacy and retention

- [ ] The lawful basis for processing attendance and biometric data is
  documented.
- [ ] Enrollment consent is handled by the device process.
- [ ] Access to attendance exports and mirrors is restricted.
- [ ] Attendance retention is defined.
- [ ] Deletion requests have a tested procedure.
- [ ] Backups follow the same retention and access rules as live data.
- [ ] Third-party processors are approved and contractually covered.
- [ ] Raw templates are not copied into the mirror or logs.

## 12. Version and change management

- [ ] The `Essl_F22_SDK` version is pinned in the lock file or requirements.
- [ ] The device model and firmware are recorded against that version.
- [ ] Upgrades are tested on a non-production device.
- [ ] The changelog is reviewed before upgrading.
- [ ] The database schema impact is understood.
- [ ] A rollback artifact (wheel or lock file) is retained.
- [ ] The branch/PR/release process in the repository is followed.
- [ ] Documentation is updated with the change.

## 13. Incident response

- [ ] The team can stop scheduled jobs quickly.
- [ ] The team can revoke database credentials.
- [ ] The team can block a user without deleting them.
- [ ] The team can restore access from recorded state.
- [ ] The team can replace the device and reconcile serial-scoped state.
- [ ] The team knows how to preserve logs for an investigation.
- [ ] The team knows not to retry destructive writes blindly.
- [ ] A post-incident review is required for access-control mistakes.

## 14. Final go/no-go

Before the first production write:

- [ ] Read-only production run succeeded.
- [ ] Mirror counts and samples match the device.
- [ ] Backup was taken and restore-tested.
- [ ] A test user was created, read, updated, and deleted successfully.
- [ ] Block and unblock were tested end-to-end on a non-production user.
- [ ] The operator has the runbook open.
- [ ] The rollback owner is available.
- [ ] The approval reference is recorded.

If any item is unchecked, do not proceed with a broad write. Resolve it or
narrow the change to a reversible test.

## Next

- [Handle errors](handle-errors.md)
- [Troubleshooting](../help/troubleshooting.md)
- [Compatibility](../help/compatibility.md)
