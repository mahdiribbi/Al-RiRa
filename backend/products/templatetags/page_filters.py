from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()


@register.filter
def render_page_content(content):
    if not content:
        return ''

    blocks = content.strip().split('\n\n')
    html_parts = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith('## '):
            heading_text = escape(block[3:].strip())
            html_parts.append(f'<h5 class="fw-bold mt-4">{heading_text}</h5>')
        else:
            para_text = escape(block).replace('\n', '<br>')
            html_parts.append(f'<p>{para_text}</p>')

    return mark_safe(''.join(html_parts))


@register.filter
def dictkey(d, key):
    return d.get(key, key)