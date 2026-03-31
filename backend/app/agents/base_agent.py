"""
BaseAgent — wraps Anthropic Claude API with tool_use support.
All 15 JADWA agents inherit from this class.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
import anthropic
from app.core.config import settings


class BaseAgent(ABC):
    """
    Base class for all JADWA AI agents.
    Provides Claude API integration, tool execution, and logging.
    """

    name: str = "BaseAgent"
    description: str = ""
    max_tokens: int = 8192
    temperature: float = 0.3  # Low for factual/analytical tasks

    def __init__(self, db=None, run_id: Optional[str] = None):
        self.db = db
        self.run_id = run_id
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.tokens_used = 0
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt for this agent — defines its role and expertise."""
        pass

    @property
    def tools(self) -> list:
        """Claude tool_use tool definitions for this agent. Override in subclasses."""
        return []

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        """Execute a tool call from Claude. Override in subclasses."""
        raise NotImplementedError(f"Tool '{tool_name}' not implemented in {self.name}")

    def run(self, context: dict) -> dict:
        """
        Main entry point. Sends context to Claude with tools,
        handles tool_use loop, returns final output dict.
        """
        self.started_at = datetime.utcnow()
        messages = [{"role": "user", "content": self._build_user_message(context)}]

        try:
            result = self._run_agent_loop(messages)
            self.completed_at = datetime.utcnow()
            self._log_to_db(context, result, status="completed")
            return result
        except Exception as e:
            self.completed_at = datetime.utcnow()
            self._log_to_db(context, {}, status="failed", error=str(e))
            raise

    def _run_agent_loop(self, messages: list) -> dict:
        """Agentic loop: keep calling Claude until no more tool_use calls."""
        while True:
            kwargs = {
                "model": settings.CLAUDE_MODEL,
                "max_tokens": self.max_tokens,
                "system": self.system_prompt,
                "messages": messages,
            }
            if self.tools:
                kwargs["tools"] = self.tools

            response = self.client.messages.create(**kwargs)
            self.tokens_used += (
                response.usage.input_tokens + response.usage.output_tokens
            )

            # Check stop reason
            if response.stop_reason == "end_turn":
                return self._parse_response(response)

            if response.stop_reason == "tool_use":
                # Execute all tool calls in this response
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_result = self.execute_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(tool_result),
                            }
                        )

                # Add assistant response + tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason
            return self._parse_response(response)

    def _parse_response(self, response) -> dict:
        """Extract text content from Claude's response."""
        text_blocks = [b.text for b in response.content if hasattr(b, "text")]
        return {"raw_output": "\n".join(text_blocks), "agent": self.name}

    def _build_user_message(self, context: dict) -> str:
        """Build the user message from context dict. Override for custom formatting."""
        import json

        return f"Analyze the following business project data and provide your analysis:\n\n{json.dumps(context, ensure_ascii=False, indent=2)}"

    def _log_to_db(
        self, input_data: dict, output_data: dict, status: str, error: str = None
    ):
        """Log agent run to agent_logs table."""
        if not self.db or not self.run_id:
            return
        try:
            from app.models.report import AgentLog

            log = (
                self.db.query(AgentLog)
                .filter(
                    AgentLog.run_id == self.run_id,
                    AgentLog.agent_name == self.name,
                )
                .first()
            )
            if log:
                log.status = status
                log.output_data = output_data
                log.error_message = error
                log.tokens_used = self.tokens_used
                log.completed_at = self.completed_at
            else:
                log = AgentLog(
                    run_id=self.run_id,
                    agent_name=self.name,
                    status=status,
                    input_data=input_data,
                    output_data=output_data,
                    error_message=error,
                    tokens_used=self.tokens_used,
                    started_at=self.started_at,
                    completed_at=self.completed_at,
                )
                self.db.add(log)
            self.db.commit()
        except Exception:
            pass  # Don't let logging failures break the pipeline
