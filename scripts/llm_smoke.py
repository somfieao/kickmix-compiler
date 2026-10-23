"""One-query smoke test: claude-agent-sdk -> Claude Code CLI -> DeepSeek.

Validates the DRSI_CLAUDE_MODEL / DRSI_CLAUDE_EFFORT overrides before any
dream-rsi budget is spent. Run with .env sourced.
"""

import asyncio
import os

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query


async def main() -> None:
    options = ClaudeAgentOptions(
        cwd=os.getcwd(),
        allowed_tools=["Read", "Grep", "Glob", "Edit", "Write", "Bash"],
        system_prompt={"type": "preset", "preset": "claude_code"},
        model=os.environ.get("DRSI_CLAUDE_MODEL") or None,
        effort=os.environ.get("DRSI_CLAUDE_EFFORT") or None,
    )
    async for msg in query(
        prompt="Do not use any tools. Reply with exactly one line: "
               "SMOKE-OK and the model name you are running as.",
        options=options,
    ):
        text = getattr(msg, "result", None)
        if isinstance(msg, ResultMessage):
            print(f"subtype={msg.subtype} turns={msg.num_turns} "
                  f"cost={msg.total_cost_usd} result={text!r}")


asyncio.run(main())
