import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

MENTION_RE = re.compile(r"@(\w+)")

PRIORITY_COLORS = {
    "high": "var(--pri-high)",
    "medium": "var(--pri-medium)",
    "low": "var(--pri-low)",
}

TYPE_COLORS = {
    "specific": "var(--type-specific)",
    "general": "var(--type-general)",
}


@register.filter
def priority_color(priority):
    return PRIORITY_COLORS.get(priority, "var(--pri-medium)")


@register.filter
def type_color(task_type):
    return TYPE_COLORS.get(task_type, "var(--type-specific)")


@register.filter
def progress_color(pct):
    try:
        pct = max(0, min(100, int(pct)))
    except (TypeError, ValueError):
        pct = 0
    hue = pct * 1.2
    return f"hsl({hue}, 72%, 45%)"


@register.filter
def mentionify(text):
    escaped = escape(text)
    highlighted = MENTION_RE.sub(r'<span class="mention">@\1</span>', escaped)
    return mark_safe(highlighted)
