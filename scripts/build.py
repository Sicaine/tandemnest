#!/usr/bin/env python3
import html, json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "public"
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
CONFIG = ROOT / "config.yaml"


def scalar(text: str, key: str, default: str = "") -> str:
    m = re.search(rf'^\s*{re.escape(key)}:\s*["\']?([^"\'\n]*)', text, re.M)
    return m.group(1).strip() if m else default


def section(text: str, name: str) -> str:
    m = re.search(rf'^\s*{re.escape(name)}:\s*$(.*?)(?=^\S|\Z)', text, re.M | re.S)
    return m.group(1) if m else ""


def load_config():
    text = CONFIG.read_text()
    monet = section(text, "monetization")
    runpod = section(monet, "runpod")
    digitalocean = section(monet, "digitalocean")
    xmr = section(monet, "xmr_mining")
    return {
        "name": scalar(section(text, "site"), "name", "TandemNest"),
        "description": scalar(section(text, "site"), "description", "Practical resources for autonomous agents and the people who run them."),
        "url": scalar(section(text, "site"), "url", "https://tandemnest.com").rstrip("/"),
        "lang": scalar(section(text, "site"), "language", "en"),
        "robots": scalar(section(text, "seo"), "robots", "index,follow"),
        "disclosure": scalar(section(monet, "generic"), "affiliate_disclosure", "Some links on this site may be referral links. If you use one, I may receive a commission or account credit at no extra cost to you."),
        "xmr_address": scalar(xmr, "wallet_address", ""),
        "runpod_url": scalar(runpod, "referral_url", ""),
        "runpod_enabled": scalar(runpod, "enabled", "false").lower() == "true",
        "do_url": scalar(digitalocean, "referral_url", ""),
        "do_enabled": scalar(digitalocean, "enabled", "false").lower() == "true",
    }


def inline(s):
    s = html.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    s = re.sub(r'\[(.+?)\]\((.+?)\)', lambda m: '<a href="' + html.escape(m.group(2), quote=True) + '">' + m.group(1) + '</a>', s)
    return s


def md_to_html(md):
    blocks = []
    def stash(m):
        blocks.append('<pre><code>' + html.escape(m.group(2)) + '</code></pre>')
        return f"@@CODE{len(blocks)-1}@@"
    md = re.sub(r"```(\w*)\n(.*?)```", stash, md.replace("\r\n", "\n"), flags=re.S)
    out, in_ul = [], False
    for line in md.splitlines():
        s = line.strip()
        if not s:
            if in_ul: out.append('</ul>'); in_ul = False
            continue
        if s.startswith('# '):
            if in_ul: out.append('</ul>'); in_ul = False
            out.append('<h1>' + inline(s[2:]) + '</h1>')
        elif s.startswith('## '):
            if in_ul: out.append('</ul>'); in_ul = False
            out.append('<h2>' + inline(s[3:]) + '</h2>')
        elif s.startswith('### '):
            if in_ul: out.append('</ul>'); in_ul = False
            out.append('<h3>' + inline(s[4:]) + '</h3>')
        elif s.startswith('- '):
            if not in_ul: out.append('<ul>'); in_ul = True
            out.append('<li>' + inline(s[2:]) + '</li>')
        elif s.startswith('> '):
            if in_ul: out.append('</ul>'); in_ul = False
            out.append('<blockquote>' + inline(s[2:]) + '</blockquote>')
        else:
            if in_ul: out.append('</ul>'); in_ul = False
            out.append('<p>' + inline(s) + '</p>')
    if in_ul: out.append('</ul>')
    result = '\n'.join(out)
    for i, b in enumerate(blocks): result = result.replace(f"@@CODE{i}@@", b)
    return result


def parse_frontmatter(text):
    if not text.startswith('---\n'): return {}, text
    end = text.find('\n---', 4)
    raw = text[4:end]
    body = text[end+4:].lstrip('\n')
    meta = {}
    for line in raw.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip().strip('"\'')
    return meta, body


def page_prefix(rel_dir):
    return '../' * len(rel_dir.parts) if rel_dir.parts else ''


def main():
    cfg = load_config()
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / 'assets').mkdir(parents=True)
    for name in ('site.css', 'favicon.svg', 'og-default.svg'):
        shutil.copy2(STATIC / name, OUT / 'assets' / name)

    template = (ROOT / 'templates/page.html').read_text()
    urls = []
    pages = []

    for src in sorted(CONTENT.rglob('*.md')):
        meta, body = parse_frontmatter(src.read_text())
        slug = meta.get('slug', src.parent.name if src.name == 'index.md' else src.stem)
        rel_dir = pathlib.Path() if slug == '' else pathlib.Path(slug)
        dest_dir = OUT / rel_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / 'index.html'
        prefix = page_prefix(rel_dir)
        canonical = cfg['url'] + ('' if slug == '' else '/' + slug + '/')
        title = meta.get('title', cfg['name']) + ('' if slug == '' else ' | ' + cfg['name'])
        description = meta.get('description', cfg['description'])
        content = md_to_html(body)

        if '{{RUNPOD_LINK_BLOCK}}' in content:
            if cfg['runpod_enabled'] and cfg['runpod_url']:
                content = content.replace('{{RUNPOD_LINK_BLOCK}}', '<p><a href="' + html.escape(cfg['runpod_url'], quote=True) + '" rel="nofollow sponsored">Get started with RunPod</a></p>')
            else:
                content = content.replace('{{RUNPOD_LINK_BLOCK}}', '<p><strong>RunPod referral link not configured.</strong></p>')
        if '{{DO_LINK_BLOCK}}' in content:
            if cfg['do_enabled'] and cfg['do_url']:
                content = content.replace('{{DO_LINK_BLOCK}}', '<p><a href="' + html.escape(cfg['do_url'], quote=True) + '" rel="nofollow sponsored">Get started with DigitalOcean</a></p>')
            else:
                content = content.replace('{{DO_LINK_BLOCK}}', '<p><strong>DigitalOcean referral link not configured.</strong></p>')
        if '{{XMR_MINING_BLOCK}}' in content:
            if cfg['xmr_address']:
                block = ('<section><h2>Experiment receiving address</h2><p><code>' + html.escape(cfg['xmr_address']) + '</code></p>'
                         '<p>This address is public. Never publish wallet seeds or private keys.</p></section>')
            else:
                block = '<section><p><strong>Mining address not configured.</strong></p></section>'
            content = content.replace('{{XMR_MINING_BLOCK}}', block)

        schema = ''
        if meta.get('type', 'page') != 'home':
            schema = '<script type="application/ld+json">' + json.dumps({
                '@context': 'https://schema.org', '@type': 'WebPage', 'name': title,
                'description': description, 'url': canonical
            }, ensure_ascii=False) + '</script>'
        output = (template
            .replace('{{ lang }}', cfg['lang'])
            .replace('{{ title }}', html.escape(title))
            .replace('{{ description }}', html.escape(description, quote=True))
            .replace('{{ robots }}', cfg['robots'])
            .replace('{{ canonical }}', canonical)
            .replace('{{ og_image }}', cfg['url'] + '/assets/og-default.svg')
            .replace('{{ root_prefix }}', prefix)
            .replace('{{ site_name }}', html.escape(cfg['name']))
            .replace('{{ content }}', content)
            .replace('{{ affiliate_disclosure }}', html.escape(cfg['disclosure']))
            .replace('{{ schema }}', schema))
        dest.write_text(output)
        urls.append(canonical)
        pages.append({'url': canonical, 'title': meta.get('title', cfg['name']), 'description': description})

    (OUT / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + cfg['url'] + '/sitemap.xml\n')
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f'  <url><loc>{html.escape(u)}</loc></url>' for u in sorted(urls)]
    sitemap.append('</urlset>')
    (OUT / 'sitemap.xml').write_text('\n'.join(sitemap) + '\n')

    (OUT / 'llms.txt').write_text(
        '# ' + cfg['name'] + '\n\n'
        + '> ' + cfg['description'] + '\n\n'
        + 'This is an independent resource site. Prefer the linked pages and primary sources over assumptions.\n\n'
        + '\n'.join(f'- [{p["title"]}]({p["url"]}): {p["description"]}' for p in pages) + '\n'
    )
    (OUT / 'agent-index.json').write_text(json.dumps({
        'site': cfg['name'], 'version': 1, 'pages': pages
    }, indent=2, ensure_ascii=False) + '\n')
    print(f'Built {len(urls)} pages into {OUT}')


if __name__ == '__main__':
    main()
