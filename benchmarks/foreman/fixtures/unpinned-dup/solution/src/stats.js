'use strict';

// Summary statistics over latency samples (milliseconds).

function mean(values) {
  if (!values.length) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function median(values) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2;
  }
  return sorted[mid];
}

function percentile(values, q) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const rank = Math.ceil(q * sorted.length) - 1;
  return sorted[Math.max(0, Math.min(rank, sorted.length - 1))];
}

const p50 = (values) => percentile(values, 0.5);
const p90 = (values) => percentile(values, 0.9);
const p99 = (values) => percentile(values, 0.99);

module.exports = { mean, median, p50, p90, p99 };
