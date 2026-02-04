#!/bin/bash
# Hook: Remind about PR creation workflow before gh pr create

cat << 'EOF'
╔════════════════════════════════════════════════════════════════════╗
║                    PR CREATION WORKFLOW REMINDER                   ║
╠════════════════════════════════════════════════════════════════════╣
║ Before creating this PR, confirm you have completed:               ║
║                                                                    ║
║ 1. ✓ Self-critique via subagent (reviewed diff for bugs/bloat)    ║
║ 2. ✓ Addressed critique feedback                                   ║
║ 3. ✓ Run validation (tests/lint/typecheck pass)                   ║
║                                                                    ║
║ After PR creation, you MUST:                                       ║
║ 4. Wait for CI checks: gh pr checks <pr-number> --watch           ║
║ 5. Fix any CI failures before considering PR ready                 ║
║                                                                    ║
║ See: .claude/skills/pr-creation.md for full workflow              ║
╚════════════════════════════════════════════════════════════════════╝
EOF
