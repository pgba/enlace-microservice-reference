from __future__ import annotations

import re
from dataclasses import dataclass

CURRENT_SCHEMA_VERSION = "1.1.0"

_SEMVER_PATTERN = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<prerelease>[0-9A-Za-z.-]+))?$"
)


@dataclass(frozen=True, slots=True)
class SchemaVersion:
    major: int
    minor: int
    patch: int
    prerelease: str | None = None

    @classmethod
    def parse(cls, value: str) -> SchemaVersion:
        match = _SEMVER_PATTERN.match(value)
        if not match:
            raise ValueError(f"Invalid semver: {value!r}")
        return cls(
            major=int(match.group("major")),
            minor=int(match.group("minor")),
            patch=int(match.group("patch")),
            prerelease=match.group("prerelease"),
        )

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            return f"{base}-{self.prerelease}"
        return base


def check_schema_compatible(expected: str, received: str) -> None:
    """Raise ValueError when received schema has an incompatible major version."""
    expected_version = SchemaVersion.parse(expected)
    received_version = SchemaVersion.parse(received)
    if received_version.major != expected_version.major:
        raise ValueError(
            f"Incompatible schema major version: expected {expected_version.major}, "
            f"got {received_version.major}"
        )
