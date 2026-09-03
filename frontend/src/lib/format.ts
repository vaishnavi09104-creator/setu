// Indian money formatting — lakh/crore, never crore-with-M.

export function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(amount);
}

export function formatLakh(amountInr: number): string {
  return `₹${(amountInr / 100000).toFixed(1)}L`;
}

export function formatCrore(amountInr: number): string {
  const cr = amountInr / 10000000;
  return `₹${cr >= 10 ? cr.toFixed(0) : cr.toFixed(1)}Cr`;
}

export function formatSmart(amountInr: number): string {
  if (amountInr >= 10000000) return formatCrore(amountInr);
  if (amountInr >= 100000) return formatLakh(amountInr);
  return `₹${formatINR(amountInr)}`;
}

export function pct(x: number, digits = 0): string {
  return `${(x * 100).toFixed(digits)}%`;
}

export function monthsAgo(days: number): string {
  const m = Math.round(days / 30.4);
  if (m <= 0) return "this month";
  if (m === 1) return "1 month ago";
  if (m < 18) return `${m} months ago`;
  return `${(days / 365).toFixed(1)} years ago`;
}

export function shortId(hash: string): string {
  return hash.replace("sha256:", "").slice(0, 8);
}
