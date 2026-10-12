"""An in-memory HTTP simulation. Never resolve a host or open a connection.

The fixture boundary applies in both modes; the teaching policy additionally
restricts secure fetches to the public HTTPS origin, including every redirect.
"""
from urllib.parse import urlsplit, urlunsplit, urljoin

PUBLIC_HOST = 'help.novacart.lab'
INTERNAL_HOST = 'ops.novacart.lab'
PROOF = 'FICTIONAL-SSRF-PROOF-7329'
MAX_HOPS = 4
PAGES = {
    f'https://{PUBLIC_HOST}/returns': {
        'title': 'NovaCart returns policy', 'classification': 'public',
        'body': ('Fictional return policy: delivered items can be reviewed within 30 days. '
                 f'An older help link is still listed: https://{PUBLIC_HOST}/legacy-returns. '
                 f'For delivery information, consult https://{PUBLIC_HOST}/delivery.'),
    },
    f'https://{PUBLIC_HOST}/delivery': {'location': '/shipping'},
    f'https://{PUBLIC_HOST}/shipping': {
        'title': 'NovaCart shipping guide', 'classification': 'public',
        'body': 'Fictional delivery guide: standard delivery takes 3–5 working days.',
    },
    f'https://{PUBLIC_HOST}/legacy-returns': {
        'location': f'http://{INTERNAL_HOST}/diagnostics',
    },
    f'http://{INTERNAL_HOST}/diagnostics': {
        'title': 'Internal support diagnostics', 'classification': 'internal',
        'body': f'Internal service record. {PROOF}. Fictional queue: returns-review. Customer access is not permitted.',
    },
}


def canonical_url(value):
    """Accept only unambiguous URLs in this fixed virtual world, in either mode."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ValueError('Use a virtual URL of 1–2048 characters.')
    if any(ord(char) <= 32 or ord(char) >= 127 for char in value) or '\\' in value:
        raise ValueError('Virtual URLs must use plain ASCII without spaces, controls or backslashes.')
    try:
        parsed = urlsplit(value)
        port = parsed.port
        host = parsed.hostname
    except ValueError:
        raise ValueError('Malformed virtual URL.') from None
    if parsed.scheme not in ('http', 'https') or host not in (PUBLIC_HOST, INTERNAL_HOST):
        raise ValueError('Only HTTP(S) URLs on the fictional help.novacart.lab and ops.novacart.lab hosts are supported. No network request was made.')
    if parsed.username is not None or parsed.password is not None or '%' in parsed.netloc:
        raise ValueError('User information and encoded hostnames are not supported.')
    if port not in (None, 443 if parsed.scheme == 'https' else 80):
        raise ValueError('Only the default HTTP(S) port is supported.')
    if parsed.query or parsed.fragment or '?' in value or '#' in value:
        raise ValueError('Use a listed virtual page without a query or fragment.')
    return urlunsplit((parsed.scheme, host, parsed.path or '/', '', ''))


def fetch_url(url, secure=False):
    """Record each destination check before retrieving a body or redirect."""
    hops, seen = [], set()
    current = url

    def failure(message, status):
        return dict(error=message, status=status, requested_url=url,
                    transport='offline simulation', hops=hops)

    for _ in range(MAX_HOPS):
        try:
            current = canonical_url(current)
        except ValueError as error:
            hops.append(dict(url=current, outcome='REJECTED', policy='Fixture boundary'))
            return failure(str(error), 400)
        hop = dict(url=current, policy='NOT CHECKED' if not secure else 'ALLOWED')
        hops.append(hop)
        parsed = urlsplit(current)
        if secure and (parsed.scheme != 'https' or parsed.hostname != PUBLIC_HOST):
            hop.update(outcome='BLOCKED', policy='DENIED')
            return failure('Destination policy: only the public HTTPS help origin is allowed. This destination was blocked before its content was read.', 403)
        if current in seen:
            hop['outcome'] = 'REDIRECT LOOP'
            return failure('Virtual redirect loop stopped.', 422)
        seen.add(current)
        page = PAGES.get(current)
        if page is None:
            hop['outcome'] = 'NOT FOUND'
            return failure('Page not found in the virtual URL catalogue. No network request was made.', 404)
        if 'location' in page:
            hop.update(outcome='REDIRECT', status=302, location=page['location'])
            current = urljoin(current, page['location'])
            continue
        hop.update(outcome='RETRIEVED', status=200)
        return dict(requested_url=url, final_url=current, status=200,
                    transport='offline simulation', hops=hops,
                    title=page['title'], classification=page['classification'], body=page['body'])
    return failure(f'Virtual fetch stopped at its {MAX_HOPS}-destination limit.', 422)
