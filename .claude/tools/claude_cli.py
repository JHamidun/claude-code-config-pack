"""Claude CLI wrapper — call Claude models via the claude CLI binary.

No API key needed — uses Claude Code's built-in authentication.
Works with any model available in Claude Code (Opus, Sonnet, Haiku).

Usage:
    from claude_cli import claude, claude_stream

    # Simple call
    result = claude("Translate to English: Привет мир")

    # With model selection
    result = claude("Fix this code", model="claude-sonnet-4-5")

    # With system prompt
    result = claude(
        "Review this function",
        system="You are a senior Python developer",
        model="claude-opus-4-6",
    )

    # Streaming (yields chunks)
    for chunk in claude_stream("Write a poem about AI"):
        print(chunk, end="")

    # Async support
    result = await claude_async("Explain quantum computing")

Recursion guard:
    A spawned agent can import this module and spawn again — unbounded nesting.
    Every spawn carries CLAUDE_CLI_DEPTH into the child; at the limit
    (CLAUDE_CLI_MAX_DEPTH, default 1) the next spawn raises RecursionGuardError
    instead of forking another tree. Pass allow_nested=True when the extra level
    is deliberate.

Install CLI:
    npm install -g @anthropic-ai/claude-code
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterator, Optional

# Auto-detect CLI path
_CLI_SEARCH_PATHS = [
    os.environ.get("CLAUDE_CLI_PATH", ""),
    shutil.which("claude") or "",
    "/usr/local/bin/claude",
    "/usr/bin/claude",
    str(Path.home() / ".npm-global" / "bin" / "claude"),
    str(Path.home() / "n" / "bin" / "claude"),
]

CLAUDE_CLI_PATH: Optional[str] = None
for p in _CLI_SEARCH_PATHS:
    if p and os.path.isfile(p):
        CLAUDE_CLI_PATH = p
        break


def _find_cli() -> str:
    """Find claude CLI binary, raise if not found."""
    if CLAUDE_CLI_PATH:
        return CLAUDE_CLI_PATH
    # Last resort: try 'claude' hoping it's in PATH
    if shutil.which("claude"):
        return "claude"
    raise FileNotFoundError(
        "claude CLI not found. Install: npm install -g @anthropic-ai/claude-code\n"
        "Or set CLAUDE_CLI_PATH env var."
    )


# ---------------------------------------------------------------------------
# Recursion guard
# ---------------------------------------------------------------------------
# An agent spawned by this wrapper can import this same wrapper and spawn again.
# Nothing in the CLI stops that: each level is a legitimate-looking process, so the
# nesting only ends when the machine runs out of RAM or the subscription rate-limits.
# The child process inherits DEPTH_ENV; if it is already at the limit we refuse to
# spawn and say why, instead of silently forking another tree.

DEPTH_ENV = "CLAUDE_CLI_DEPTH"
MAX_DEPTH_ENV = "CLAUDE_CLI_MAX_DEPTH"
DEFAULT_MAX_DEPTH = 1  # depth 0 = top level; 1 nested child is allowed, its child is not


class RecursionGuardError(RuntimeError):
    """Refused to spawn a nested claude CLI — the nesting limit is already reached."""


def current_depth() -> int:
    """Nesting depth of THIS process (0 = not spawned by claude_cli)."""
    try:
        return max(0, int(os.environ.get(DEPTH_ENV, "0")))
    except ValueError:
        return 0


def max_depth() -> int:
    try:
        return max(0, int(os.environ.get(MAX_DEPTH_ENV, DEFAULT_MAX_DEPTH)))
    except ValueError:
        return DEFAULT_MAX_DEPTH


def check_recursion(allow_nested: bool = False) -> int:
    """Raise RecursionGuardError if spawning would exceed the nesting limit.

    Returns the depth the child will run at. Set allow_nested=True (or raise
    CLAUDE_CLI_MAX_DEPTH) only when the extra level is deliberate.
    """
    depth = current_depth()
    limit = max_depth()
    if not allow_nested and depth >= limit:
        raise RecursionGuardError(
            f"refusing to spawn a nested claude CLI: already running at depth {depth} "
            f"(limit {limit}, env {DEPTH_ENV}={os.environ.get(DEPTH_ENV)!r}).\n"
            f"  An agent spawning itself recurses without bound.\n"
            f"  If this nesting is intended: set {MAX_DEPTH_ENV}={depth + 1} "
            f"or pass allow_nested=True."
        )
    return depth + 1


def child_env(allow_nested: bool = False, base: Optional[dict] = None) -> dict:
    """Environment for the spawned CLI, carrying the incremented depth marker."""
    env = dict(os.environ if base is None else base)
    env[DEPTH_ENV] = str(check_recursion(allow_nested))
    return env


def claude(
    prompt: str,
    *,
    system: str = "",
    model: str = "claude-sonnet-4-5",
    timeout: float = 300.0,
    max_tokens: int = 0,
    temperature: float = 0,
    output_format: str = "text",
    allow_nested: bool = False,
) -> str:
    """Call Claude via CLI. Returns response text.

    Args:
        prompt: User prompt (passed via stdin to avoid OS arg limits)
        system: System prompt (optional)
        model: Model name (default: claude-sonnet-4-5)
        timeout: Timeout in seconds (default: 300)
        max_tokens: accepted for signature compatibility and IGNORED — the CLI has
            no output-token flag (see note below). Cap length in the prompt instead.
        temperature: Temperature (0 = deterministic)
        output_format: "text" or "json"
        allow_nested: Permit one more nesting level (see check_recursion)

    Returns:
        Response text from Claude

    Raises:
        FileNotFoundError: If claude CLI is not installed
        TimeoutError: If call exceeds timeout
        RuntimeError: If CLI returns non-zero exit code
        RecursionGuardError: If already at the nesting limit
    """
    cli = _find_cli()
    env = child_env(allow_nested)

    # Flag names verified against the CLI, not guessed: the system prompt flag is
    # --system-prompt (--system does not exist and makes the CLI exit non-zero),
    # and there is no max-tokens flag at all. Sending the wrong name here turns
    # every call into "Claude CLI error (exit 1)" with an unhelpful stderr.
    cmd = [cli, "-p", "--model", model, "--output-format", output_format]
    if system:
        cmd.extend(["--system-prompt", system])

    full_prompt = prompt

    try:
        proc = subprocess.run(
            cmd,
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Claude CLI timed out after {timeout}s")

    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        raise RuntimeError(f"Claude CLI error (exit {proc.returncode}): {stderr}")

    return proc.stdout.strip()


def claude_stream(
    prompt: str,
    *,
    system: str = "",
    model: str = "claude-sonnet-4-5",
    timeout: float = 300.0,
    allow_nested: bool = False,
) -> Iterator[str]:
    """Stream Claude response. Yields text chunks.

    Args:
        prompt: User prompt
        system: System prompt (optional)
        model: Model name
        timeout: Timeout in seconds
        allow_nested: Permit one more nesting level (see check_recursion)

    Yields:
        Text chunks as they arrive
    """
    cli = _find_cli()
    env = child_env(allow_nested)

    # stream-json needs all three flags together: without --verbose the CLI emits
    # no stream_event at all and the loop below silently yields nothing.
    cmd = [cli, "-p", "--model", model, "--output-format", "stream-json",
           "--include-partial-messages", "--verbose"]
    if system:
        cmd.extend(["--system-prompt", system])

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    # Send prompt and close stdin
    proc.stdin.write(prompt)
    proc.stdin.close()

    streamed_any = False
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                etype = event.get("type")
                if etype == "stream_event":
                    # Partial-message frames. Only text_delta goes out: thinking_delta
                    # is the model's reasoning and must not reach the caller as answer.
                    delta = event.get("event", {}).get("delta", {})
                    if delta.get("type") == "text_delta" and delta.get("text"):
                        streamed_any = True
                        yield delta["text"]
                elif etype == "assistant" and "content" in event:
                    streamed_any = True
                    yield event["content"]
                elif etype == "text":
                    streamed_any = True
                    yield event.get("text", "")
                elif etype == "result":
                    # Final aggregate. Emitting it after deltas would duplicate the
                    # whole answer, so it is only a fallback when nothing streamed.
                    text = event.get("result", "")
                    if text and not streamed_any:
                        yield text
            except json.JSONDecodeError:
                # Plain text fallback
                yield line
    finally:
        proc.wait(timeout=10)
        if proc.returncode and proc.returncode != 0:
            stderr = proc.stderr.read().strip()
            if stderr:
                raise RuntimeError(f"Claude CLI error: {stderr}")


async def claude_async(
    prompt: str,
    *,
    system: str = "",
    model: str = "claude-sonnet-4-5",
    timeout: float = 300.0,
    max_tokens: int = 0,
    output_format: str = "text",
    allow_nested: bool = False,
) -> str:
    """Async version of claude(). Runs CLI in a thread pool.

    Same args as claude(). Returns response text.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: claude(
            prompt,
            system=system,
            model=model,
            timeout=timeout,
            max_tokens=max_tokens,
            output_format=output_format,
            allow_nested=allow_nested,
        ),
    )


def claude_json(
    prompt: str,
    *,
    system: str = "",
    model: str = "claude-sonnet-4-5",
    timeout: float = 300.0,
    allow_nested: bool = False,
) -> dict:
    """Call Claude and parse response as JSON.

    Args:
        prompt: Should request JSON output
        system: System prompt (optional)
        model: Model name
        timeout: Timeout in seconds

    Returns:
        Parsed JSON dict
    """
    raw = claude(
        prompt,
        system=system,
        model=model,
        timeout=timeout,
        output_format="json",
        allow_nested=allow_nested,
    )
    return json.loads(raw)


def validate_response(
    original: str,
    response: str,
    min_ratio: float = 0.3,
    max_ratio: float = 3.0,
) -> tuple[bool, str]:
    """Validate LLM response against original text.

    Checks for:
    - Chatty prefixes ("Here is the corrected text...")
    - Length ratio anomalies
    - Empty responses

    Returns:
        (is_valid, cleaned_response_or_error_message)
    """
    if not response.strip():
        return False, "Empty response"

    # Strip chatty prefixes
    chatty_prefixes = [
        "Here is", "Вот исправленный", "Вот откорректированный",
        "Ниже приведён", "Исправленный текст:", "Corrected text:",
    ]
    cleaned = response.strip()
    for prefix in chatty_prefixes:
        if cleaned.startswith(prefix):
            # Find the actual content after the prefix line
            lines = cleaned.split("\n", 1)
            if len(lines) > 1:
                cleaned = lines[1].strip()
            break

    # Length ratio check
    if original.strip():
        ratio = len(cleaned) / len(original)
        if ratio < min_ratio:
            return False, f"Response too short (ratio {ratio:.2f})"
        if ratio > max_ratio:
            return False, f"Response too long (ratio {ratio:.2f})"

    return True, cleaned


# CLI entrypoint for quick testing
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python claude_cli.py 'your prompt here' [--model MODEL]")
        print(f"CLI path: {CLAUDE_CLI_PATH or 'not found'}")
        sys.exit(1)

    prompt_text = sys.argv[1]
    model_name = "claude-sonnet-4-5"

    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model_name = sys.argv[idx + 1]

    print(claude(prompt_text, model=model_name))
