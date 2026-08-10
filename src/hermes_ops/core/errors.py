"""Expected domain errors shown without tracebacks."""


class HermesOpsError(Exception):
    """Base class for expected errors."""


class PathResolutionError(HermesOpsError):
    """A supplied project path cannot be resolved."""


class ConfigurationError(HermesOpsError):
    """Base class for configuration failures."""


class ConfigurationMissingError(ConfigurationError):
    """The required configuration file does not exist."""


class ConfigurationSyntaxError(ConfigurationError):
    """The configuration is not valid TOML."""


class ConfigurationSchemaError(ConfigurationError):
    """The TOML document does not match the supported schema."""


class ConfigurationUnsafePathError(ConfigurationError):
    """The configuration path uses a symlink, junction, or reparse point."""


class SkillContractError(HermesOpsError):
    """A SKILL.md file cannot be loaded under the version 1 contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class SkillRegistryError(HermesOpsError):
    """Skill discovery cannot produce a valid immutable registry."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
