# Project: streamdeck-utils

Windows-only Stream Deck plugin with mic mute toggle (pycaw) and auto-discovery Python script runner.

## Pre-commit Requirements

Before every commit, you MUST run both of these agents from `~/.claude/agents/`:

1. **network-audit** — Scan all plugin source files for outbound network calls. This plugin must NEVER make external network requests. Local WebSocket connections to 127.0.0.1 (Stream Deck SDK) are expected and safe.

2. **security-reviewer** — Scan all plugin source files for secrets, API keys, PII, hardcoded user paths, path traversal vulnerabilities, and dangerous operations. Flag anything suspicious for user approval.

Both agents must PASS before committing. If either flags an issue, fix it first.
