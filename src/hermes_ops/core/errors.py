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


class SkillCatalogError(HermesOpsError):
    """The catalog owned by the installed Hermes distribution is unavailable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class SkillPolicyError(HermesOpsError):
    """Skill planning cannot produce a plan under the supplied policy."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class SkillExecutionError(HermesOpsError):
    """A planned skill cannot cross the closed execution boundary."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class AnalysisError(HermesOpsError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ExecutionBudgetError(HermesOpsError):
    """The pure execution budget contract was used with invalid inputs."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ExecutionBudgetExceeded(ExecutionBudgetError):
    """An action would exceed the absolute execution budget."""

    def __init__(self, message: str) -> None:
        super().__init__("EXECUTION_BUDGET_EXCEEDED", message)


class ExecutionBudgetReserved(ExecutionBudgetError):
    """An action would consume units reserved for a later category."""

    def __init__(self, message: str) -> None:
        super().__init__("EXECUTION_BUDGET_RESERVED", message)


class CheckpointRequired(ExecutionBudgetError):
    """Exploration must stop so execution can prepare safe closure."""

    def __init__(self, message: str) -> None:
        super().__init__("EXECUTION_CHECKPOINT_REQUIRED", message)
