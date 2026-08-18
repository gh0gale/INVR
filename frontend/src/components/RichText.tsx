/**
 * Renders the light markdown the models actually emit.
 *
 * The prompts ask for "Header: Content" blocks with headers marked in double
 * asterisks, so that markup arrived on screen as literal `**` characters. This
 * turns it into real typography.
 *
 * It builds React elements rather than setting innerHTML, so model output is
 * never interpreted as HTML. Anything it does not recognise is left as plain
 * text, which is the safe failure.
 */
import React from 'react';

/** Splits a line on **bold** and *emphasis* runs. */
function inline(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  // Non-greedy, so adjacent runs on one line stay separate.
  const pattern = /(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`\n]+`)/g;
  const parts = text.split(pattern).filter((p) => p !== '');

  parts.forEach((part, i) => {
    const key = `${keyPrefix}-${i}`;
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      nodes.push(
        <strong key={key} className="font-bold text-fg">
          {part.slice(2, -2)}
        </strong>,
      );
    } else if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      nodes.push(
        <span key={key} className="tabular-nums text-fg">
          {part.slice(1, -1)}
        </span>,
      );
    } else if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      nodes.push(
        <em key={key} className="not-italic font-medium text-fg">
          {part.slice(1, -1)}
        </em>,
      );
    } else {
      nodes.push(<React.Fragment key={key}>{part}</React.Fragment>);
    }
  });

  return nodes;
}

const BULLET = /^\s*[-*•]\s+/;
const NUMBERED = /^\s*\d+[.)]\s+/;

/**
 * A line is a heading when it is entirely wrapped in asterisks, or when it is
 * a short "Header:" lead-in with nothing after the colon. A "Header: content"
 * line on one row keeps the header bold and the content normal.
 */
function headingParts(line: string): { head: string; rest: string } | null {
  const whole = line.match(/^\*\*(.+?)\*\*:?\s*$/);
  if (whole) return { head: whole[1].trim().replace(/:$/, ''), rest: '' };

  // Models put the colon either inside or outside the asterisks. Accept both.
  const lead = line.match(/^\*\*(.+?)\*\*\s*:?\s*(.+)$/);
  if (lead) return { head: lead[1].trim().replace(/:$/, ''), rest: lead[2].trim() };

  // Plain "Header: content" where the header is short and title-like.
  const plain = line.match(/^([A-Z][A-Za-z0-9 /&()-]{2,44}):\s*(.*)$/);
  if (plain && !BULLET.test(line)) return { head: plain[1].trim(), rest: plain[2].trim() };

  return null;
}

export const RichText: React.FC<{ text: string; className?: string }> = ({
  text,
  className = '',
}) => {
  const lines = (text ?? '').replace(/\r\n/g, '\n').split('\n');
  const blocks: React.ReactNode[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;

  const flushList = (key: string) => {
    if (!list) return;
    const Tag = list.ordered ? 'ol' : 'ul';
    blocks.push(
      <Tag key={key} className="flex flex-col gap-1.5 pl-1">
        {list.items.map((item, i) => (
          <li key={i} className="flex gap-2.5">
            <span aria-hidden="true" className="select-none pt-[0.15em] text-fg-3">
              {list?.ordered ? `${i + 1}.` : '–'}
            </span>
            <span>{inline(item, `li-${key}-${i}`)}</span>
          </li>
        ))}
      </Tag>,
    );
    list = null;
  };

  lines.forEach((raw, i) => {
    const line = raw.trimEnd();

    if (line.trim() === '') {
      flushList(`l-${i}`);
      return;
    }

    if (BULLET.test(line) || NUMBERED.test(line)) {
      const ordered = NUMBERED.test(line);
      const item = line.replace(BULLET, '').replace(NUMBERED, '');
      if (!list || list.ordered !== ordered) {
        flushList(`l-${i}`);
        list = { ordered, items: [] };
      }
      list.items.push(item);
      return;
    }

    flushList(`l-${i}`);

    const heading = headingParts(line);
    if (heading) {
      blocks.push(
        <div key={`h-${i}`} className="flex flex-col gap-0.5">
          <h4 className="text-base font-bold tracking-tight text-fg">{heading.head}</h4>
          {heading.rest && <p>{inline(heading.rest, `hr-${i}`)}</p>}
        </div>,
      );
      return;
    }

    blocks.push(<p key={`p-${i}`}>{inline(line, `p-${i}`)}</p>);
  });

  flushList('tail');

  return <div className={`flex flex-col gap-3 ${className}`}>{blocks}</div>;
};
