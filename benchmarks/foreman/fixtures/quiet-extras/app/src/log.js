'use strict';

// Log line builders. Each level formats its own line.
// TODO: these four are the same function with a different label — collapse them.

function debug(msg) {
  return `[${new Date(0).toISOString()}] DEBUG ${String(msg).trim()}`;
}

function info(msg) {
  return `[${new Date(0).toISOString()}] INFO ${String(msg).trim()}`;
}

function warn(msg) {
  return `[${new Date(0).toISOString()}] WARN ${String(msg).trim()}`;
}

function error(msg) {
  return `[${new Date(0).toISOString()}] ERROR ${String(msg).trim()}`;
}

module.exports = { debug, info, warn, error };
