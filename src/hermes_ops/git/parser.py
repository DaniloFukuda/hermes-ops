from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorktreeChanges:
    modified: tuple[str, ...] = ()
    added: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    untracked: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()

    @property
    def clean(self) -> bool:
        return not any(
            (self.modified, self.added, self.removed, self.untracked, self.conflicts)
        )


_CONFLICT_CODES = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}


def parse_porcelain_v1_z(output: str) -> WorktreeChanges:
    modified: list[str] = []
    added: list[str] = []
    removed: list[str] = []
    untracked: list[str] = []
    conflicts: list[str] = []
    records = output.split("\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            raise ValueError(f"Malformed Git porcelain record: {record!r}")
        xy, path = record[:2], record[3:]
        if xy == "??":
            untracked.append(path)
            continue
        if xy == "!!":
            continue
        if xy in _CONFLICT_CODES:
            conflicts.append(path)
            continue
        if "R" in xy or "C" in xy:
            if index >= len(records) or not records[index]:
                raise ValueError("Rename/copy record is missing its source path")
            index += 1
        if "A" in xy:
            added.append(path)
        if "D" in xy:
            removed.append(path)
        if "M" in xy or "T" in xy or "R" in xy or "C" in xy:
            modified.append(path)
    return WorktreeChanges(
        tuple(modified),
        tuple(added),
        tuple(removed),
        tuple(untracked),
        tuple(conflicts),
    )

