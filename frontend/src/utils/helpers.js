export const formatNumber = (value, digits = 2) => {
  const number = Number(value);
  return Number.isFinite(number)
    ? number.toLocaleString(undefined, { maximumFractionDigits: digits })
    : '-';
};

export const sanitizeText = (input) => {
  if (!input && input !== 0) return '';
  let text = String(input);
  // Strip HTML tags
  text = text.replace(/\<[^\>]+\>/g, '');
  // Remove common filler phrases
  text = text.replace(/skip to (main|content)/gi, '');
  // Clean up dashes and separators
  text = text.replace(/^\s*-+\s*|\s*-+\s*$/g, '');
  text = text.replace(/\s*\|\s*/g, ' - ');
  text = text.replace(/[\u2013\u2014-]{2,}/g, '-');
  // Remove leading home keywords
  if (/^home\b/i.test(text)) text = text.replace(/^home\b[\s:-]*/i, '');
  // Collapse whitespace
  text = text.replace(/\s+/g, ' ').trim();
  // Trim surrounding punctuation
  text = text.replace(/^[|\-:\s]+|[|\-:\s]+$/g, '');
  return text;
};
