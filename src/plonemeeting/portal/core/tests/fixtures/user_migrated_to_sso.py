# -*- coding: utf-8 -*-
"""Context the `user_migrated_to_sso` mail is previewed with.

One dict named CONTEXT, and it is the template's contract: `bin/preview-emails`
renders with it, and a `${...}` added to the template without a key added here
renders empty rather than raising. One key per placeholder and no more ; the
names `render()` injects (`lang`, `theme` and its tokens, `portal_url`,
`preheader`) are deliberately absent, since pinning them here would hide a
broken injection and freeze every preview to one language.

Values chosen to expose a bug rather than to look tidy: an accented institution
name, an address long enough to make the card wrap, and a login url with a
query string that has to survive escaping.
"""

CONTEXT = {
    "institution": "Commune de Braine-le-Château",
    "email": "jeanne.vandermeulen@braine-le-chateau.be",
    "username": "jvandermeulen",
    "login_url": (
        "https://www.deliberations.be/acl_users/oidc/login"
        "?came_from=https%3A//www.deliberations.be/braine-le-chateau"
    ),
    "account_url": "https://auth.imio.be/realms/deliberations/account/",
}
