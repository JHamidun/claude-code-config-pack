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


def claude(
    prompt: str,
    *,
    system: str = "",
    model: str = "claude-sonnet-4-5",
    timeout: float = 300.0,
    max_tokens: int = 0,
    temperature: float = 0,
    output_format: str = "text",
) -> str:
    """Call Claude via CLI. Returns response text.

    Args:
        prompt: User prompt (passed via stdin to avoid OS arg limits)
        system: System prompt (optional)
        model: Model name (default: claude-sonnet-4-5)
        timeout: Timeout in seconds (default: 300)
        max_tokens: Max output tokens (0 = model default)
        temperature: Temperature (0 = deterministic)
        output_format: "text" or "json"

    Returns:
        Response text from Claude

    Raises:
        FileNotFoundError: If claude CLI is not installed
        TimeoutError: If call exceeds timeout
        RuntimeError: If CLI returns non-zero exit code
    """
    cli = _find_cli()

    cmd = [cli, "-p", "--model", model, "--output-format", output_format]
    if system:
        cmd.extend(["--system", system])
    if max_tokens > 0:
        cmd.extend(["--max-tokens", str(max_tokens)])

    full_prompt = prompt
    if system and "--system" not in cmd:
        full_prompt = f"{system}\n\n{prompt}"

    try:
        proc = subprocess.run(
            cmd,
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
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
) -> Iterator[str]:
    """Stream Claude response. Yields text chunks.

    Args:
        prompt: User prompt
        system: System prompt (optional)
        model: Model name
        timeout: Timeout in seconds

    Yields:
        Text chunks as they arrive
    """
    cli = _find_cli()

    cmd = [cli, "-p", "--model", model, "--output-format", "stream-json"]
    if system:
        cmd.extend(["--system", system])

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Send prompt and close stdin
    proc.stdin.write(prompt)
    proc.stdin.close()

    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("type") == "assistant" and "content" in event:
                    yield event["content"]
                elif event.get("type") == "text":
                    yield event.get("text", "")
                elif event.get("type") == "result":
                    text = event.get("result", "")
                    if text:
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
        ),
    )


def claude_json(
    prompt: str,
    *,
    system: str = "",
    model: str = "claude-sonnet-4-5",
    timeout: float = 300.0,
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
def _print_usage():
    print("Usage: python claude_cli.py 'your prompt here' [--model MODEL]")
    print("Calls the live claude CLI binary (needs Claude Code installed and authenticated).")
    print(f"CLI path: {CLAUDE_CLI_PATH or 'not found'}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        _print_usage()
        sys.exit(1)
    if argv[0] in ("-h", "--help"):
        _print_usage()
        sys.exit(0)
    if argv[0].startswith("-"):
        print(f"ERROR: expected a prompt as the first argument, got option {argv[0]!r}", file=sys.stderr)
        _print_usage()
        sys.exit(2)

    prompt_text = argv[0]
    model_name = "claude-sonnet-4-5"

    if "--model" in argv:
        idx = argv.index("--model")
        if idx + 1 < len(argv):
            model_name = argv[idx + 1]

    print(claude(prompt_text, model=model_name))
