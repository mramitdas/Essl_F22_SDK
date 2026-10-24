"""Typed storage methods implemented over a small document primitive."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from datetime import datetime

from essl_f22.errors import StateStoreError
from essl_f22.models import (
    AttendanceRecord,
    DeviceInfo,
    GroupInfo,
    TimeZone,
    User,
    UserTimeZone,
)
from essl_f22.storage.codec import (
    Document,
    attendance_record_document,
    attendance_record_from_document,
    attendance_record_key,
    block_timezone_document,
    block_timezone_from_document,
    device_info_document,
    device_info_from_document,
    fingerprint_metadata_document,
    fingerprint_metadata_from_document,
    group_document,
    group_from_document,
    sync_state_document,
    sync_state_from_document,
    timezone_document,
    timezone_from_document,
    user_document,
    user_from_document,
    user_timezone_document,
    user_timezone_from_document,
)
from essl_f22.storage.models import (
    AttendanceEntry,
    BlockTimeZoneState,
    FingerprintMetadata,
    SyncState,
)


class DocumentStorage(ABC):
    """Storage backend built from namespace/key JSON document primitives."""

    @abstractmethod
    def read_document(self, namespace: str, key: str) -> Document | None: ...

    @abstractmethod
    def write_document(
        self, namespace: str, key: str, document: Mapping[str, object]
    ) -> None: ...

    @abstractmethod
    def delete_document(self, namespace: str, key: str) -> None: ...

    @abstractmethod
    def list_documents(self, namespace: str) -> dict[str, Document]: ...

    @abstractmethod
    def replace_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> None: ...

    @abstractmethod
    def upsert_documents(
        self, namespace: str, documents: Mapping[str, Mapping[str, object]]
    ) -> int: ...

    @abstractmethod
    def clear_namespace(self, namespace: str) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @staticmethod
    def _namespace(collection: str, device_serial: str) -> str:
        return f"{collection}:{device_serial}"

    def get_original_user_timezone(
        self, device_serial: str, uid: int
    ) -> UserTimeZone | None:
        namespace = self._namespace("block_original_user_timezone", device_serial)
        document = self.read_document(namespace, str(uid))
        return None if document is None else user_timezone_from_document(document)

    def save_original_user_timezone(
        self, device_serial: str, uid: int, timezone: UserTimeZone
    ) -> None:
        if timezone.uid != uid:
            raise StateStoreError(
                f"timezone uid {timezone.uid} does not match requested uid {uid}"
            )
        namespace = self._namespace("block_original_user_timezone", device_serial)
        self.write_document(namespace, str(uid), user_timezone_document(timezone))

    def delete_original_user_timezone(self, device_serial: str, uid: int) -> None:
        namespace = self._namespace("block_original_user_timezone", device_serial)
        self.delete_document(namespace, str(uid))

    def list_blocked_uids(self, device_serial: str) -> list[int]:
        namespace = self._namespace("block_original_user_timezone", device_serial)
        uids = [
            user_timezone_from_document(document).uid
            for document in self.list_documents(namespace).values()
        ]
        return sorted(uids)

    def get_block_timezone(self, device_serial: str) -> BlockTimeZoneState | None:
        document = self.read_document("block_timezone", device_serial)
        return None if document is None else block_timezone_from_document(document)

    def save_block_timezone(self, device_serial: str, slot: int) -> None:
        self.write_document(
            "block_timezone",
            device_serial,
            block_timezone_document(BlockTimeZoneState(slot)),
        )

    def save_device_info(self, device_serial: str, info: DeviceInfo) -> None:
        self.write_document("device_info", device_serial, device_info_document(info))

    def get_device_info(self, device_serial: str) -> DeviceInfo | None:
        document = self.read_document("device_info", device_serial)
        return None if document is None else device_info_from_document(document)

    def replace_users(self, device_serial: str, users: Iterable[User]) -> None:
        documents = {str(user.uid): user_document(user) for user in users}
        self.replace_documents(self._namespace("users", device_serial), documents)

    def list_users(self, device_serial: str) -> list[User]:
        namespace = self._namespace("users", device_serial)
        users = [
            user_from_document(document)
            for document in self.list_documents(namespace).values()
        ]
        return sorted(users, key=lambda user: user.uid)

    def get_user(self, device_serial: str, uid: int) -> User | None:
        namespace = self._namespace("users", device_serial)
        document = self.read_document(namespace, str(uid))
        return None if document is None else user_from_document(document)

    def replace_groups(self, device_serial: str, groups: Iterable[GroupInfo]) -> None:
        documents = {str(group.group_id): group_document(group) for group in groups}
        self.replace_documents(self._namespace("groups", device_serial), documents)

    def list_groups(self, device_serial: str) -> list[GroupInfo]:
        namespace = self._namespace("groups", device_serial)
        groups = [
            group_from_document(document)
            for document in self.list_documents(namespace).values()
        ]
        return sorted(groups, key=lambda group: group.group_id)

    def get_group(self, device_serial: str, group_id: int) -> GroupInfo | None:
        namespace = self._namespace("groups", device_serial)
        document = self.read_document(namespace, str(group_id))
        return None if document is None else group_from_document(document)

    def replace_timezones(
        self, device_serial: str, timezones: Mapping[int, TimeZone]
    ) -> None:
        documents = {
            str(slot): timezone_document(timezone)
            for slot, timezone in timezones.items()
        }
        self.replace_documents(self._namespace("timezones", device_serial), documents)

    def list_timezones(self, device_serial: str) -> dict[int, TimeZone]:
        namespace = self._namespace("timezones", device_serial)
        timezones = [
            timezone_from_document(document)
            for document in self.list_documents(namespace).values()
        ]
        return {
            timezone.slot: timezone
            for timezone in sorted(timezones, key=lambda t: t.slot)
        }

    def get_timezone(self, device_serial: str, slot: int) -> TimeZone | None:
        namespace = self._namespace("timezones", device_serial)
        document = self.read_document(namespace, str(slot))
        return None if document is None else timezone_from_document(document)

    def replace_fingerprints(
        self, device_serial: str, fingerprints: Iterable[FingerprintMetadata]
    ) -> None:
        documents = {
            f"{fingerprint.uid}:{fingerprint.fid}": fingerprint_metadata_document(
                fingerprint
            )
            for fingerprint in fingerprints
        }
        self.replace_documents(
            self._namespace("fingerprints", device_serial), documents
        )

    def list_fingerprints(self, device_serial: str) -> list[FingerprintMetadata]:
        namespace = self._namespace("fingerprints", device_serial)
        fingerprints = [
            fingerprint_metadata_from_document(document)
            for document in self.list_documents(namespace).values()
        ]
        return sorted(fingerprints, key=lambda item: (item.uid, item.fid))

    def upsert_attendance(
        self, device_serial: str, entries: Iterable[AttendanceEntry]
    ) -> int:
        documents = {
            entry.record_key or attendance_record_key(entry.record): (
                attendance_record_document(entry.record)
            )
            for entry in entries
        }
        return self.upsert_documents(
            self._namespace("attendance", device_serial), documents
        )

    def replace_attendance(
        self, device_serial: str, entries: Iterable[AttendanceEntry]
    ) -> None:
        documents = {
            entry.record_key or attendance_record_key(entry.record): (
                attendance_record_document(entry.record)
            )
            for entry in entries
        }
        self.replace_documents(self._namespace("attendance", device_serial), documents)

    def list_attendance(
        self,
        device_serial: str,
        *,
        uid: int | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[AttendanceRecord]:
        namespace = self._namespace("attendance", device_serial)
        records = [
            attendance_record_from_document(document)
            for document in self.list_documents(namespace).values()
        ]
        if uid is not None:
            records = [record for record in records if record.uid == uid]
        if since is not None:
            records = [record for record in records if record.timestamp >= since]
        if until is not None:
            records = [record for record in records if record.timestamp <= until]
        records.sort(
            key=lambda record: (record.timestamp, attendance_record_key(record))
        )
        if limit is not None:
            records = records[:limit]
        return records

    def attendance_count(self, device_serial: str) -> int:
        return len(self.list_documents(self._namespace("attendance", device_serial)))

    def save_sync_state(self, device_serial: str, state: SyncState) -> None:
        self.write_document("sync_state", device_serial, sync_state_document(state))

    def get_sync_state(self, device_serial: str) -> SyncState | None:
        document = self.read_document("sync_state", device_serial)
        return None if document is None else sync_state_from_document(document)

    def clear_device(self, device_serial: str) -> None:
        for collection in (
            "users",
            "groups",
            "timezones",
            "fingerprints",
            "attendance",
            "block_original_user_timezone",
        ):
            self.clear_namespace(self._namespace(collection, device_serial))
        self.delete_document("device_info", device_serial)
        self.delete_document("sync_state", device_serial)
        self.delete_document("block_timezone", device_serial)
