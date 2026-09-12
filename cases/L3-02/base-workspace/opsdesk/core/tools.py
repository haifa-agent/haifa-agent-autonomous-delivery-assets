"""Tool definitions exposed to the operator assistant."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolParameter:
    name: str
    type: str
    required: bool = False
    description: str = ""


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: tuple[ToolParameter, ...]

    def parameter(self, name: str) -> ToolParameter:
        for parameter in self.parameters:
            if parameter.name == name:
                return parameter
        raise KeyError(name)


SEND_NOTIFICATION = ToolDefinition(
    name="send_notification",
    description="Send a notification to an operator channel.",
    parameters=(
        ToolParameter("channel", "string", required=True, description="Target channel, e.g. email or sms."),
        ToolParameter("message", "string", required=True, description="Notification body."),
        ToolParameter("urgent", "boolean", description="Page the on-call operator."),
    ),
)

TOOLS: dict[str, ToolDefinition] = {SEND_NOTIFICATION.name: SEND_NOTIFICATION}
