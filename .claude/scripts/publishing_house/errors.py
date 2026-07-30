class PublishingHouseError(Exception):
    """Base framework error."""


class ConfigurationError(PublishingHouseError):
    """Configuration is absent or invalid."""


class ProjectNotFoundError(PublishingHouseError):
    """A requested project does not exist."""


class ValidationFailure(PublishingHouseError):
    """Schema or invariant validation failed."""


class StateTransitionError(PublishingHouseError):
    """A workflow transition is not permitted."""


class ApprovalError(PublishingHouseError):
    """An approval is absent, stale, invalid, or out of scope."""


class RightsError(PublishingHouseError):
    """Rights evidence does not permit the requested operation."""


class BuildError(PublishingHouseError):
    """A format build failed or lacks required inputs."""


class SecurityError(PublishingHouseError):
    """A path or operation violates the local security boundary."""
