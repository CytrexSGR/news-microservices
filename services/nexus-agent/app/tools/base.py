"""Base tool class for NEXUS agent."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field
import time

from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolResult(BaseModel):
    """Result from tool execution."""

    success: bool = Field(description="Whether tool execution succeeded")
    data: Any = Field(default=None, description="Tool result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: int = Field(default=0, description="Execution time in milliseconds")
    tool_name: str = Field(default="", description="Name of the tool that was executed")


class BaseTool(ABC):
    """Abstract base class for all NEXUS tools."""

    name: str = "base_tool"
    description: str = "Base tool description"

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

    async def run(self, **kwargs) -> ToolResult:
        """Run tool with timing and error handling."""
        start_time = time.time()

        try:
            logger.info(
                "tool_execution_start",
                tool=self.name,
                args=kwargs,
            )

            result = await self.execute(**kwargs)
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            result.tool_name = self.name

            logger.info(
                "tool_execution_complete",
                tool=self.name,
                success=result.success,
                execution_time_ms=result.execution_time_ms,
            )

            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)

            logger.error(
                "tool_execution_error",
                tool=self.name,
                error=str(e),
            )

            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
                tool_name=self.name,
            )
