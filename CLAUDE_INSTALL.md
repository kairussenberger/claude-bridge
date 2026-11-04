# Installing ClaudeBridge — instructions for Claude

You (Claude / Claude Code) are installing a Fusion add-in that lets you run
Python against the Autodesk Fusion API on the user's machine. Follow these
steps in order. Do not skip the verification step.

## What this is

- `addin/ClaudeBridge/` is a Fusion add-in. When running, it serves HTTP on
  `127.0.0.1:47621` (localhost only) and executes posted Python on Fusion's
  main thread via a custom event.
- Requests must carry header `X-Token: <contents of ~/.fusion_bridge_token>`.
  The add-in creates that token file (mode 600) on first start.
- `fusion.py` is the client you will use afterwards.

Tell the user, before installing, in one sentence: this add-in lets any local
process that can read `~/.fusion_bridge_token` run arbitrary code inside
Fusion; it only listens on localhost.

## Steps

1. **Check prerequisites.**
   - macOS: `ls "$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API"`
     must exist (Fusion installed and launched at least once). If missing, stop
     and ask the user to install/launch Fusion.
   - Windows: the target folder is
     `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`. `install.sh` does not
     support Windows; copy `addin\ClaudeBridge` there manually.
   - `python3` must be available (the client is stdlib-only, Python 3.8+).

2. **Install.** From the repo root run `./install.sh`. It copies the add-in into
   Fusion's AddIns folder and symlinks `fusion.py` to `~/.local/bin/fusion`.
   Re-running it is safe (it overwrites the add-in files — do this after
   pulling updates, then restart the add-in in Fusion).

3. **Ask the user to start the add-in.** You cannot do this yourself. Tell them:
   > In Fusion press **Shift+S** → **Add-Ins** tab → select **ClaudeBridge** →
   > **Run**. Tick **Run on Startup** if you want it always on.

   Wait for them to confirm.

4. **Verify.**
   ```bash
   fusion --ping                       # -> {"ok": true, "bridge": "ClaudeBridge"}
   fusion 'result = app.version'       # -> Fusion version string
   ```
   If `--ping` says *connection refused*, the add-in isn't running (back to
   step 3). If `/exec` returns 403, the token file doesn't match — the add-in
   read the token when it started; restart the add-in. A 504 means Fusion is
   busy or a modal dialog is open.

5. **Report** to the user that the bridge is installed and responding.

## Using the bridge

```bash
fusion 'code'            # run code
fusion -f script.py      # run a file
echo 'code' | fusion     # from stdin
fusion --ping
```

Inside the code: `adsk`, `app`, `ui`, `design` (active product cast to
`adsk.fusion.Design`, may be `None`) are predefined. Assign to `result` to get
a value back (non-JSON values come back as `repr`); `print()` output is
returned too. The global scope **persists between calls**, so define helpers
once and reuse them.

## Gotchas (learned the hard way)

- **Never walk the whole Data Panel in one call.** Recursively iterating
  `app.data.dataHubs → dataProjects → dataFolders/dataFiles` does lazy cloud
  fetches on Fusion's main thread and has crashed Fusion outright. List
  projects first, then one project/folder per call.
- Your code runs on Fusion's **main thread** — long loops freeze the UI. Keep
  calls short; the client's timeout is 300 s.
- A modal dialog open in Fusion blocks every call (you'll get a 504).
- Setting `occurrence.transform2` only persists after `design.snapshots.add()`
  (or call `revertPendingSnapshot`).
- Positions the user dragged without capturing read back as identity — don't
  "move relative" without checking.
- Bodies created inside a base feature lose their names — rename after
  `finishEdit()`.
- Visual checks: `app.activeViewport.saveAsImageFile(path, w, h)`, then read the
  image. Collision checks: `design.analyzeInterference(...)`.
- Joint limits are enforced during timeline replay; avoid limits on joints that
  are driven in the history.
- Undo: `ui.commandDefinitions.itemById("UndoCommand").execute()` (async, one
  step per call; watch `design.timeline.count`).
- Never destroy or overwrite user documents without asking; save copies
  instead.
