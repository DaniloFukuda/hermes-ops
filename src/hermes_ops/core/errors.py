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


class SpecParsingError(HermesOpsError):
    """Raised when a specification file cannot be parsed."""

    def __init__(self, message: str, *, code: str = "invalid_hybrid_format"):
        super().__init__(message)
        self.code = code


__all__ = [
    "HermesOpsError",
    "PathResolutionError",
    "ConfigurationError",
    "ConfigurationMissingError",
    "ConfigurationSyntaxError",
    "ConfigurationSchemaError",
    "ConfigurationUnsafePathError",
    "SpecParsingError",
]
