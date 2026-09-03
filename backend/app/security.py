"""app.security — role scoping via X-Demo-Role header (demo auth).

Production would be JWT/OIDC — a middleware change, and we say so when asked
rather than pretending this is production auth.
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException

ROLES = ("corporate", "ngo", "auditor", "admin")

ROLE_MODEL = {
    "corporate": "corp_demo",
    "ngo": "ngo_demo",
    "auditor": "audit_demo",
    "admin": "admin_demo",
}


def current_role(x_demo_role: str | None = Header(default=None)) -> str:
    if not x_demo_role or x_demo_role not in ROLES:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "ROLE_REQUIRED",
                    "message": "Set the X-Demo-Role header to one of: " + ", ".join(ROLES),
                    "detail": {},
                }
            },
        )
    return x_demo_role


def require_role(*allowed: str):
    """FastAPI dependency enforcing role membership on a route."""

    def dep(role: str = Depends(current_role)) -> str:
        if role not in allowed:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "FORBIDDEN_ROLE",
                        "message": f"Role '{role}' may not access this resource.",
                        "detail": {"allowed": list(allowed)},
                    }
                },
            )
        return role

    return dep
