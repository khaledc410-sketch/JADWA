"""
BaseAgent — wraps Anthropic Claude API with tool_use support.
All 15 JADWA agents inherit from this class.
"""

from abc import ABC, abstractmethod
import concurrent.futures
from datetime import datetime
import json
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
        import time as _time

        while True:
            kwargs = {
                "model": settings.CLAUDE_MODEL,
                "max_tokens": self.max_tokens,
                "system": self.system_prompt,
                "messages": messages,
            }
            if self.tools:
                kwargs["tools"] = self.tools

            # Retry with exponential backoff for rate limits
            max_retries = 8
            for attempt in range(max_retries):
                try:
                    response = self.client.messages.create(**kwargs)
                    break
                except Exception as e:
                    if "429" in str(e) or "rate_limit" in str(e):
                        wait = min(2**attempt * 5, 120)  # 5s, 10s, 20s, ... max 120s
                        _time.sleep(wait)
                        if attempt == max_retries - 1:
                            raise
                    else:
                        raise
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

    def _parse_json_output(self, raw: str) -> dict:
        """Try to parse JSON from Claude's text response."""
        try:
            # Try direct parse
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
        # Try to extract JSON block from markdown
        if "```json" in raw:
            start = raw.index("```json") + 7
            end = raw.index("```", start)
            try:
                return json.loads(raw[start:end])
            except (json.JSONDecodeError, ValueError):
                pass
        if "```" in raw:
            start = raw.index("```") + 3
            end = raw.index("```", start)
            try:
                return json.loads(raw[start:end])
            except (json.JSONDecodeError, ValueError):
                pass
        # Try to find JSON object in text
        for i, c in enumerate(raw):
            if c == "{":
                try:
                    return json.loads(raw[i:])
                except json.JSONDecodeError:
                    continue
        return {"raw_output": raw}

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


class SubAgentOrchestrator(BaseAgent):
    """
    Orchestrator that runs multiple specialized sub-agents in parallel,
    then feeds all outputs to a reviewer agent for synthesis.

    Subclass and override:
      - get_sub_agents(context) -> list of BaseAgent instances
      - reviewer_system_prompt -> str
      - name, description
    """

    reviewer_max_tokens: int = 8192
    reviewer_temperature: float = 0.2

    @abstractmethod
    def get_sub_agents(self, context: dict) -> list:
        """Return list of sub-agent instances to run in parallel."""
        pass

    @property
    @abstractmethod
    def reviewer_system_prompt(self) -> str:
        """System prompt for the reviewer agent that synthesizes sub-agent outputs."""
        pass

    @property
    def system_prompt(self) -> str:
        return self.reviewer_system_prompt

    def run(self, context: dict) -> dict:
        """
        1. Run all sub-agents in parallel
        2. Collect their outputs
        3. Feed all outputs to reviewer agent for synthesis
        4. Return reviewer's final output
        """
        self.started_at = datetime.utcnow()

        try:
            # Step 1: Get sub-agents
            sub_agents = self.get_sub_agents(context)
            sub_results = {}

            # Step 2: Run sub-agents (limited concurrency to avoid API rate limits)
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(2, len(sub_agents))
            ) as executor:
                future_map = {}
                for agent in sub_agents:
                    future = executor.submit(agent.run, context)
                    future_map[future] = agent.name

                for future in concurrent.futures.as_completed(future_map):
                    agent_name = future_map[future]
                    try:
                        result = future.result(timeout=300)
                        sub_results[agent_name] = result
                    except Exception as e:
                        sub_results[agent_name] = {
                            "error": str(e),
                            "status": "failed",
                        }

            # Step 3: Run reviewer to synthesize
            reviewer_context = {
                "sub_agent_outputs": sub_results,
                "original_context": context,
            }
            result = self._run_reviewer(reviewer_context)

            self.completed_at = datetime.utcnow()

            # Sum up tokens from all sub-agents
            for agent in sub_agents:
                self.tokens_used += agent.tokens_used

            self._log_to_db(context, result, status="completed")
            return result

        except Exception as e:
            self.completed_at = datetime.utcnow()
            self._log_to_db(context, {}, status="failed", error=str(e))
            raise

    def _run_reviewer(self, reviewer_context: dict) -> dict:
        """Run the reviewer agent to synthesize all sub-agent outputs."""
        messages = [
            {
                "role": "user",
                "content": (
                    "You have received outputs from multiple specialized sub-agents. "
                    "Review, cross-validate, and synthesize them into a single cohesive output.\n\n"
                    "Sub-agent outputs:\n"
                    f"{json.dumps(reviewer_context['sub_agent_outputs'], ensure_ascii=False, indent=2)}\n\n"
                    "Original project context:\n"
                    f"{json.dumps(reviewer_context['original_context'], ensure_ascii=False, indent=2)}\n\n"
                    "Return a JSON object with the final synthesized analysis. "
                    "Resolve any conflicts between sub-agents by choosing the most reliable data. "
                    "No text outside the JSON block."
                ),
            }
        ]

        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=self.reviewer_max_tokens,
            temperature=self.reviewer_temperature,
            system=self.reviewer_system_prompt,
            messages=messages,
        )
        self.tokens_used += response.usage.input_tokens + response.usage.output_tokens

        text = "\n".join(b.text for b in response.content if hasattr(b, "text"))
        return self._parse_json_output(text)
