"""Human confirmation logic, kept out of the UI so it can be unit-tested."""
from __future__ import annotations

from .schemas import Checklist, ReviewStatus


class ExportBlockedError(Exception):
    """Raised when an export is requested before all required items are reviewed."""


def apply_review(checklist: Checklist, key: str, action: ReviewStatus | str,
                 user_value=None, note: str | None = None) -> None:
    item = checklist.get(key)
    if item is None:
        raise KeyError(f"No checklist item '{key}'.")
    action = ReviewStatus(action)
    if action == ReviewStatus.EDITED:
        if user_value in (None, "", []):
            raise ValueError("An edited item needs a new value.")
        item.user_value = user_value
    else:
        item.user_value = None
    item.review_status = action
    item.user_note = note or None


def progress(checklist: Checklist) -> tuple[int, int]:
    """(reviewed required items, total required items)."""
    req = [i for i in checklist.items if i.required]
    return sum(i.review_status != ReviewStatus.PENDING for i in req), len(req)


def require_ready(checklist: Checklist) -> None:
    if not checklist.ready_to_export():
        done, total = progress(checklist)
        pending = [i.label for i in checklist.items if i.required and i.review_status == ReviewStatus.PENDING]
        raise ExportBlockedError(f"Review all required items first ({done}/{total} done). "
                                 f"Pending: {', '.join(pending)}.")


def parse_user_value(text: str, is_list: bool):
    """UI helper: one item per line for list fields."""
    if is_list:
        items = [ln.strip("-• \t") for ln in text.splitlines()]
        return [i for i in items if i] or None
    return text.strip() or None
