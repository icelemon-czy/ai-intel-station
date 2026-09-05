# claude-code

> Claude Code is an agentic coding tool that lives in your terminal, understands your codebase, and helps you code faster by executing routine tasks, explaining complex code, and handling git workflows - all through natural language commands.

- ⭐ Stars: 143337
- 🏷️ Language: Python
- 🌐 URL: https://github.com/anthropics/claude-code
- 📅 Created: 2025-02-22
- 🔄 Updated: 2026-08-29

## Open Issues
- [#90528] [enhancement] [FEATURE] Add an interactive "human-assist" mode for GUI/emulator actions in Claude Code / Claude Desktop (@al-chris)
- [#90527] [bug, has repro, platform:macos, area:auth] macOS: Claude Code accumulates a new Keychain credential entry per login (110 in 5 weeks) and fails to reuse them, causing repeated forced re-auth (@m7tt-h)
- [#90526] [bug, platform:linux, area:core, platform:vscode, area:cli] [Bug] Resume flag incorrectly interprets system message as user input (@shoddyguard)
- [#90525] [bug, duplicate] Symlinked rule directories load from user-level ~/.claude/rules/ but never from project-level .claude/rules/ (2.1.241, 2.1.251) (@FANTASYSSL)
- [#90524] [bug, has repro, platform:macos, area:bash] Case-insensitive collision in project temp-dir path breaks Bash entirely after a case-only rename (macOS/APFS) (@meganemura)
- [#90523] [bug, has repro, platform:macos, area:core] Project-level .claude/rules/ symlinks (files and directories) are never loaded — neither at startup nor via paths: trigger (2.1.241, 2.1.251) (@FANTASYSSL)
- [#90522] [bug, platform:macos, area:model] Single prompt loop from safeguards (@washyaderner)
- [#90521] [bug, has repro, area:claude-code-web, platform:web, area:networking, area:sandbox] [BUG] Cloud sandbox proxy resets Chromium's TLS 1.3 handshake; WebKit unaffected (corrects #11791) (@charlieatgc)
- [#90520] [enhancement, area:agents, area:desktop, area:agent-view] [FEATURE] Allow resuming or reading the transcript of a completed/expired subagent (@maximsv2-sudo)
- [#90519] [bug, platform:windows, area:plugins] plugin update --scope project can update the wrong repository, silently, and report success (@yigitdenktas)
- [#90518] [bug, platform:macos, area:model, needs-repro] [Bug] Unrelated safety filter blocking legitimate Bluetooth operations (@jdkruzr)
- [#90517] [bug, area:model, model] [MODEL] (@Soreth81)
- [#90516] [bug, area:model, model] [Fable] Claude presents implementation conclusions without direct source inspectio (@robinhuisma)
- [#90515] [bug, has repro, platform:linux, regression, area:cli, area:plugins] Plugin slash-commands return "Unknown command" in headless (-p) mode on 2.1.251 — regression from 2.1.250 (@jokkopucko)
- [#90514] [bug, platform:windows, area:tui, area:model] [Bug] Claude Opus 5 model shows degraded performance and unexpected behavior changes (@henrychinchilla)
- [#90513] [enhancement, platform:macos] [Feature Request] Add time tracking integration for work clock in/out automation (@kakuxishun)
- [#90512] [bug, platform:windows, area:desktop, area:chrome] [BUG] Desktop app: input box floods with endless [ / 「 characters (IME composition) while claude-in-chrome browser-selection dialog is open (@jena-teachers)
- [#90511] [enhancement, area:cowork, area:integrations] Bridge/notification channel between a Claude Code session and Claude Desktop (@AnalystHero)
- [#90510] [bug, duplicate, platform:macos, area:model] [Bug] Reasoning extraction flag triggered despite explicit "not hidden reasoning" instruction (@lucasban)
- [#90509] [bug, has repro, platform:windows, area:cost, area:core] [BUG] Context silently loses 157K tokens with no compaction record, then prompt cache thrashes for 17 minutes (@ahmed-alshalabi)
