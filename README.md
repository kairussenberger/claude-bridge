# ClaudeBridge for Autodesk Fusion

A tiny Fusion add-in plus a stdlib-only Python client that let
[Claude Code](https://claude.com/claude-code) drive Autodesk Fusion live: run
API code, inspect and edit designs, take viewport screenshots.

```
Claude Code ──fusion.py──▶ HTTP 127.0.0.1:47621 ──custom event──▶ Fusion main thread (exec)
```

## Install

Easiest: open this repo in Claude Code and say *"install this"*. Claude follows
[`CLAUDE_INSTALL.md`](CLAUDE_INSTALL.md).

Manually (macOS):

```bash
./install.sh
# In Fusion: Shift+S → Add-Ins → ClaudeBridge → Run
fusion --ping
```

## Use

```bash
fusion 'result = design.rootComponent.name'
fusion -f script.py
```

`adsk`, `app`, `ui`, `design` are predefined; assign `result` to return a value.
The scope persists between calls. See `CLAUDE_INSTALL.md` for gotchas.

## Security

The add-in executes arbitrary Python inside Fusion. It binds to localhost only
and requires the token in `~/.fusion_bridge_token` (created on first run,
mode 600). Stop the add-in when you don't need it.
