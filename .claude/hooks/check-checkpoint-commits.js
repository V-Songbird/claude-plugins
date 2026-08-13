let input = '';
process.stdin.on('data', d => { input += d; });
process.stdin.on('end', () => {
  let data;
  try { data = JSON.parse(input); } catch { process.exit(0); }
  const command = data && data.tool_input && data.tool_input.command || '';
  if (!/git\s+commit\b/.test(command)) process.exit(0);
  const msgMatch = command.match(/-m\s+["']([^"']*)["']/);
  const message = msgMatch ? msgMatch[1] : command;
  if (/\btask\s+\d+\s*\/\s*\d+\s*:/i.test(message)) {
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PostToolUse',
        additionalContext: 'This looks like a per-step checkpoint commit ("task N/M:"). Per-step checkpoints are working state, not deliverable history: branch first, checkpoint on the branch, then `git merge --squash` back and commit once with a real message before reporting.'
      }
    }));
  }
  process.exit(0);
});
