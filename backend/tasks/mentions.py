import re

MENTION_RE = re.compile(r"@([A-Za-z0-9_]+)")
RESERVED_MENTIONS = {"admin", "supervisor"}


def parse_mention_names(text):
    return MENTION_RE.findall(text or "")


def mention_targets(people):
    """Names offered in the autocomplete dropdown: each person's first
    name (falling back to username), plus the reserved broadcast words."""
    names = []
    seen = set()
    for person in people:
        handle = person.user.first_name or person.user.username
        if handle.lower() not in seen:
            seen.add(handle.lower())
            names.append(handle)
    names.extend(["Supervisor", "Admin"])
    return names


def resolve_mention_recipients(text, people, exclude=None):
    """Given comment text and the full list of Person, return the set of
    Person who should be notified. @Name matches that person's first name,
    username, or full display name (case-insensitive). @Admin / @Supervisor
    notify every admin, since they aren't tied to one specific account."""
    mentioned = {name.lower() for name in parse_mention_names(text)}
    if not mentioned:
        return set()

    recipients = set()
    for person in people:
        candidates = {
            c.lower()
            for c in [person.user.first_name, person.user.username, str(person)]
            if c
        }
        if candidates & mentioned:
            recipients.add(person)

    if mentioned & RESERVED_MENTIONS:
        recipients.update(p for p in people if p.role == "admin")

    if exclude is not None:
        recipients.discard(exclude)

    return recipients
