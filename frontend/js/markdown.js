/* Small, safe Markdown renderer. All input is HTML-escaped first, so output can't inject markup. */
const Markdown = (() => {
  const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  const esc = (s) => s.replace(/[&<>"']/g, (c) => ESC[c]);

  function inline(raw) {
    let s = esc(raw);
    const codes = [];
    s = s.replace(/`([^`\n]+)`/g, (_, c) => { codes.push(c); return '\u0000' + (codes.length - 1) + '\u0000'; });
    s = s.replace(/\*\*([^*\n]+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/(^|[^*\w])\*([^*\s][^*\n]*?)\*(?![*\w])/g, '$1<em>$2</em>');
    s = s.replace(/~~([^~\n]+?)~~/g, '<del>$1</del>');
    s = s.replace(/\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    return s.replace(/\u0000(\d+)\u0000/g, (_, i) => '<code>' + codes[i] + '</code>');
  }

  const FENCE = /^\s*```\s*([\w+#.-]*)\s*$/;
  const FENCE_END = /^\s*```\s*$/;
  const HEADING = /^(#{1,4})\s+(.*)$/;
  const HR = /^\s*([-*_])\1\1+\s*$/;
  const QUOTE = /^\s*>/;
  const ITEM = /^(\s*)([-*+]|\d+[.)])\s+(.*)$/;
  const TABLE_ROW = /^\s*\|.*\|\s*$/;
  const TABLE_SEP = /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/;

  function codeBlock(lang, code) {
    return '<div class="code-block"><div class="code-head"><span>' + esc(lang || 'code') +
      '</span><button type="button" class="copy-code" aria-label="Copy code">Copy</button></div>' +
      '<pre><code>' + esc(code) + '</code></pre></div>';
  }

  function renderItems(items, idx, indent) {
    const tag = items[idx].ordered ? 'ol' : 'ul';
    let html = '<' + tag + '>';
    let i = idx;
    while (i < items.length && items[i].indent >= indent) {
      if (items[i].indent > indent || items[i].ordered !== items[idx].ordered) break;
      let li = inline(items[i].text);
      i++;
      if (i < items.length && items[i].indent > indent) {
        const nested = renderItems(items, i, items[i].indent);
        li += nested.html;
        i = nested.next;
      }
      html += '<li>' + li + '</li>';
    }
    return { html: html + '</' + tag + '>', next: i };
  }

  const cells = (line) => line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((c) => c.trim());

  function isBlockStart(line, next) {
    return FENCE.test(line) || HEADING.test(line) || HR.test(line) || QUOTE.test(line) || ITEM.test(line) ||
      (TABLE_ROW.test(line) && next !== undefined && TABLE_SEP.test(next));
  }

  function render(text) {
    const lines = String(text).replace(/\r\n?/g, '\n').split('\n');
    const out = [];
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      let m;

      if ((m = line.match(FENCE))) {
        const code = [];
        i++;
        while (i < lines.length && !FENCE_END.test(lines[i])) code.push(lines[i++]);
        i++;
        out.push(codeBlock(m[1], code.join('\n')));
        continue;
      }
      if (!line.trim()) { i++; continue; }
      if ((m = line.match(HEADING))) {
        out.push('<h' + m[1].length + '>' + inline(m[2]) + '</h' + m[1].length + '>');
        i++; continue;
      }
      if (HR.test(line)) { out.push('<hr>'); i++; continue; }
      if (QUOTE.test(line)) {
        const q = [];
        while (i < lines.length && QUOTE.test(lines[i])) q.push(lines[i++].replace(/^\s*>\s?/, ''));
        out.push('<blockquote>' + render(q.join('\n')) + '</blockquote>');
        continue;
      }
      if (TABLE_ROW.test(line) && i + 1 < lines.length && TABLE_SEP.test(lines[i + 1])) {
        const head = cells(line);
        i += 2;
        const rows = [];
        while (i < lines.length && TABLE_ROW.test(lines[i])) rows.push(cells(lines[i++]));
        out.push('<table><thead><tr>' + head.map((c) => '<th>' + inline(c) + '</th>').join('') + '</tr></thead><tbody>' +
          rows.map((r) => '<tr>' + r.map((c) => '<td>' + inline(c) + '</td>').join('') + '</tr>').join('') +
          '</tbody></table>');
        continue;
      }
      if (ITEM.test(line)) {
        const items = [];
        while (i < lines.length) {
          const im = lines[i].match(ITEM);
          if (im) {
            items.push({ indent: im[1].replace(/\t/g, '    ').length, ordered: /\d/.test(im[2]), text: im[3] });
            i++;
          } else if (!lines[i].trim() && i + 1 < lines.length && ITEM.test(lines[i + 1])) {
            i++;
          } else break;
        }
        let k = 0;
        while (k < items.length) {
          const r = renderItems(items, k, items[k].indent);
          out.push(r.html);
          k = r.next;
        }
        continue;
      }
      const para = [];
      while (i < lines.length && lines[i].trim() && !(para.length && isBlockStart(lines[i], lines[i + 1]))) {
        para.push(inline(lines[i++]));
      }
      out.push('<p>' + para.join('<br>') + '</p>');
    }
    return out.join('');
  }

  return { render };
})();
