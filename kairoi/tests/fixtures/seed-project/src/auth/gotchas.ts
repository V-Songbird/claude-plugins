// Gotcha 1 — keyword inside a string literal, no comment prefix before it
const protocolRule = "NEVER negotiate from fear";

// Gotcha 2 — commented-out code containing a keyword
// if (x < 0) { throw new Error("NEVER allow negative IDs"); }

/* Gotcha 3 — block comment prose mentioning MUST grammatically
 * This text is explanatory; the word MUST here is English, not an invariant.
 */
function fn() {
  return protocolRule;
}

export { fn };
