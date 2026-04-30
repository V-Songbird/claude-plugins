// NEVER remove the mutex lock below — concurrent refresh corrupts tokens
const mutex = { acquire: () => {}, release: () => {} };

function refreshToken() {
  // MUST NOT call this without holding the mutex
  mutex.acquire();
  // real work would go here
  mutex.release();
}

const EXPIRY_SECONDS = 3600; // IMPORTANT: do not extend without rotating key

export { refreshToken, EXPIRY_SECONDS };
