import type { ReactNode } from "react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

function parseInlineFormatting(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining) {
    // Inline code `code`
    const codeMatch = remaining.match(/^`([^`]+)`/);
    if (codeMatch) {
      parts.push(
        <code
          key={key++}
          className="rounded-md bg-muted/60 px-1.5 py-0.5 font-mono text-[0.85em] font-medium text-foreground"
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
      // Stray character
      parts.push(remaining[0]);
      remaining = remaining.slice(1);
    } else {
      parts.push(remaining.slice(0, nextSpecial));
      remaining = remaining.slice(nextSpecial);
    }
  }

  return parts;
}

export function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  if (!content) {
    return <p className="text-sm text-muted">No content available.</p>;
  }

  const lines = content.split("\n");
  const elements: ReactNode[] = [];
  let i = 0;
  let elementKey = 0;

  while (i < lines.length) {
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
      i++; // Skip closing ```

      elements.push(
        <div
          key={elementKey++}
          className="my-4 overflow-hidden rounded-xl border border-subtle bg-surface-2/80 shadow-xs"
        >
          <div className="flex items-center justify-between border-b border-subtle bg-surface-2 px-4 py-1.5 text-xs text-muted font-mono">
            <span>{lang}</span>
          </div>
          <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-foreground">
            <code>{codeLines.join("\n")}</code>
          </pre>
        </div>
      );
      continue;
    }

    // Headings #, ##, ###
    if (line.startsWith("# ")) {
      elements.push(
        <h1
          key={elementKey++}
          className="mt-6 mb-3 text-2xl font-bold tracking-tight text-foreground sm:text-3xl"
        >
          {parseInlineFormatting(line.slice(2))}
        </h1>
      );
      i++;
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h2
          key={elementKey++}
          className="mt-5 mb-2.5 text-xl font-bold tracking-tight text-foreground sm:text-2xl"
        >
          {parseInlineFormatting(line.slice(3))}
        </h2>
      );
      i++;
      continue;
    }
    if (line.startsWith("### ")) {
      elements.push(
        <h3
          key={elementKey++}
          className="mt-4 mb-2 text-lg font-semibold tracking-tight text-foreground"
        >
          {parseInlineFormatting(line.slice(4))}
        </h3>
      );
      i++;
      continue;
    }

    // Blockquote >
    if (line.startsWith("> ")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].startsWith("> ")) {
        quoteLines.push(lines[i].slice(2));
        i++;
      }
      elements.push(
        <blockquote
          key={elementKey++}
          className="my-3 border-l-2 border-accent pl-4 text-sm italic text-muted"
        >
          {quoteLines.map((ql, qIdx) => (
            <p key={qIdx}>{parseInlineFormatting(ql)}</p>
          ))}
        </blockquote>
      );
      continue;
    }

    // List item - or *
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      const listItems: string[] = [];
      while (
        i < lines.length &&
        (lines[i].trim().startsWith("- ") || lines[i].trim().startsWith("* "))
      ) {
        listItems.push(lines[i].trim().slice(2));
        i++;
      }
      elements.push(
        <ul key={elementKey++} className="my-3 list-disc space-y-1.5 pl-6 text-sm text-foreground">
          {listItems.map((item, idx) => (
            <li key={idx}>{parseInlineFormatting(item)}</li>
          ))}
        </ul>
      );
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
      !lines[i].startsWith("#") &&
      !lines[i].startsWith(">") &&
      !lines[i].trim().startsWith("```") &&
      !lines[i].trim().startsWith("- ") &&
      !lines[i].trim().startsWith("* ")
    ) {
      paragraphLines.push(lines[i]);
      i++;
    }

    elements.push(
      <p key={elementKey++} className="my-2.5 text-sm leading-relaxed text-foreground/90">
        {parseInlineFormatting(paragraphLines.join(" "))}
      </p>
    );
  }

  return <div className={`prose-container ${className}`}>{elements}</div>;
}
