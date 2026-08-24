import type { ReactNode } from "react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
  compact?: boolean;
}

function parseInlineFormatting(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  let remaining = text;
  let key = 0;
  let safetyCounter = 0;
  const maxIterations = remaining.length * 2 + 100;

  while (remaining && safetyCounter++ < maxIterations) {
    // Inline code `code`
    const codeMatch = remaining.match(/^`([^`]+)`/);
    if (codeMatch) {
      parts.push(
        <code
          key={key++}
          className="rounded bg-muted/60 px-1 py-0.5 font-mono text-[0.85em] font-medium text-foreground"
        >
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.slice(codeMatch[0].length);
      continue;
    }

    // Bold **bold**
    const boldMatch = remaining.match(/^\*\*([^*]+)\*\*/);
    if (boldMatch) {
      parts.push(
        <strong key={key++} className="font-semibold text-foreground">
          {boldMatch[1]}
        </strong>
      );
      remaining = remaining.slice(boldMatch[0].length);
      continue;
    }

    // Italic *italic* or _italic_
    const italicMatch = remaining.match(/^(\*|_)([^*_]+)\1/);
    if (italicMatch) {
      parts.push(
        <em key={key++} className="italic text-foreground">
          {italicMatch[2]}
        </em>
      );
      remaining = remaining.slice(italicMatch[0].length);
      continue;
    }

    // Link [label](href)
    const linkMatch = remaining.match(/^\[([^\]]+)\]\(([^)]+)\)/);
    if (linkMatch) {
      parts.push(
        <a
          key={key++}
          href={linkMatch[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-accent underline underline-offset-2 hover:text-accent-hover"
        >
          {linkMatch[1]}
        </a>
      );
      remaining = remaining.slice(linkMatch[0].length);
      continue;
    }

    // Plain text until next markdown delimiter
    const nextSpecial = remaining.search(/[`*_\[]/);
    if (nextSpecial === -1) {
      parts.push(remaining);
      break;
    } else if (nextSpecial === 0) {
      parts.push(remaining[0]);
      remaining = remaining.slice(1);
    } else {
      parts.push(remaining.slice(0, nextSpecial));
      remaining = remaining.slice(nextSpecial);
    }
  }

  return parts;
}

export function MarkdownRenderer({ content, className = "", compact = false }: MarkdownRendererProps) {
  if (!content) {
    return <p className="text-xs text-muted">No content available.</p>;
  }

  const lines = content.split("\n");
  const elements: ReactNode[] = [];
  let i = 0;
  let elementKey = 0;
  let safetyLoopCounter = 0;
  const maxLineIterations = lines.length * 2 + 100;

  while (i < lines.length && safetyLoopCounter++ < maxLineIterations) {
    const line = lines[i];

    // Fenced Code Block ```lang
    if (line.trim().startsWith("```")) {
      const lang = line.trim().slice(3).trim() || "code";
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) {
        i++; // Skip closing ```
      }

      elements.push(
        <div
          key={elementKey++}
          className={`overflow-hidden rounded-lg border border-subtle bg-surface-2/80 shadow-xs ${
            compact ? "my-2" : "my-4"
          }`}
        >
          <div className="flex items-center justify-between border-b border-subtle bg-surface-2 px-3 py-1 text-[11px] text-muted font-mono">
            <span>{lang}</span>
          </div>
          <pre
            className={`overflow-x-auto font-mono leading-relaxed text-foreground ${
              compact ? "p-2.5 text-[11px]" : "p-4 text-xs"
            }`}
          >
            <code>{codeLines.join("\n")}</code>
          </pre>
        </div>
      );
      continue;
    }

    // Horizontal Rules (---, ***, ___)
    if (/^(\*{3,}|-{3,}|_{3,})$/.test(line.trim())) {
      elements.push(<hr key={elementKey++} className={compact ? "my-2 border-subtle" : "my-4 border-subtle"} />);
      i++;
      continue;
    }

    // Headings #, ##, ###, ####, #####, ######
    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const text = headingMatch[2];
      if (level === 1) {
        elements.push(
          <h1
            key={elementKey++}
            className={
              compact
                ? "mt-2.5 mb-1 text-sm font-bold tracking-tight text-foreground"
                : "mt-6 mb-3 text-2xl font-bold tracking-tight text-foreground sm:text-3xl"
            }
          >
            {parseInlineFormatting(text)}
          </h1>
        );
      } else if (level === 2) {
        elements.push(
          <h2
            key={elementKey++}
            className={
              compact
                ? "mt-2 mb-1 text-xs font-bold tracking-tight text-foreground"
                : "mt-5 mb-2.5 text-xl font-bold tracking-tight text-foreground sm:text-2xl"
            }
          >
            {parseInlineFormatting(text)}
          </h2>
        );
      } else {
        elements.push(
          <h3
            key={elementKey++}
            className={
              compact
                ? "mt-1.5 mb-0.5 text-xs font-semibold tracking-tight text-foreground"
                : "mt-4 mb-2 text-lg font-semibold tracking-tight text-foreground"
            }
          >
            {parseInlineFormatting(text)}
          </h3>
        );
      }
      i++;
      continue;
    }

    // Blockquote >
    if (line.startsWith(">")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].startsWith(">")) {
        quoteLines.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      elements.push(
        <blockquote
          key={elementKey++}
          className={
            compact
              ? "my-1.5 border-l-2 border-accent pl-2.5 text-xs italic text-muted"
              : "my-3 border-l-2 border-accent pl-4 text-sm italic text-muted"
          }
        >
          {quoteLines.map((ql, qIdx) => (
            <p key={qIdx}>{parseInlineFormatting(ql)}</p>
          ))}
        </blockquote>
      );
      continue;
    }

    // List item - or * or 1.
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ") || /^\d+\.\s+/.test(line.trim())) {
      const isOrdered = /^\d+\.\s+/.test(line.trim());
      const listItems: string[] = [];
      while (
        i < lines.length &&
        (lines[i].trim().startsWith("- ") ||
          lines[i].trim().startsWith("* ") ||
          /^\d+\.\s+/.test(lines[i].trim()))
      ) {
        const itemText = lines[i].trim().replace(/^(\*|-|\d+\.)\s+/, "");
        listItems.push(itemText);
        i++;
      }

      if (isOrdered) {
        elements.push(
          <ol
            key={elementKey++}
            className={`list-decimal text-foreground ${
              compact ? "my-1 space-y-0.5 pl-4 text-xs" : "my-3 space-y-1.5 pl-6 text-sm"
            }`}
          >
            {listItems.map((item, idx) => (
              <li key={idx}>{parseInlineFormatting(item)}</li>
            ))}
          </ol>
        );
      } else {
        elements.push(
          <ul
            key={elementKey++}
            className={`list-disc text-foreground ${
              compact ? "my-1 space-y-0.5 pl-4 text-xs" : "my-3 space-y-1.5 pl-6 text-sm"
            }`}
          >
            {listItems.map((item, idx) => (
              <li key={idx}>{parseInlineFormatting(item)}</li>
            ))}
          </ul>
        );
      }
      continue;
    }

    // Empty line
    if (!line.trim()) {
      i++;
      continue;
    }

    // Paragraph
    const paragraphLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].match(/^#{1,6}\s+/) &&
      !lines[i].startsWith(">") &&
      !lines[i].trim().startsWith("```") &&
      !lines[i].trim().startsWith("- ") &&
      !lines[i].trim().startsWith("* ") &&
      !/^\d+\.\s+/.test(lines[i].trim()) &&
      !/^(\*{3,}|-{3,}|_{3,})$/.test(lines[i].trim())
    ) {
      paragraphLines.push(lines[i]);
      i++;
    }

    if (paragraphLines.length > 0) {
      elements.push(
        <p
          key={elementKey++}
          className={
            compact
              ? "my-1 text-xs leading-relaxed text-foreground/90"
              : "my-2.5 text-sm leading-relaxed text-foreground/90"
          }
        >
          {parseInlineFormatting(paragraphLines.join(" "))}
        </p>
      );
    } else {
      // Guaranteed forward progress
      i++;
    }
  }

  return <div className={`prose-container ${className}`}>{elements}</div>;
}
