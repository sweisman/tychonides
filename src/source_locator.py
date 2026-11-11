"""Public page locators when a printed numeral cannot be established."""

import re
from itertools import pairwise


def validate_page_locator(value):
    ranged = isinstance(value, dict) and "source_pdf_pages" in value
    page_key = "source_pdf_pages" if ranged else "source_pdf_page"
    pages = value.get(page_key) if isinstance(value, dict) else None
    valid_pages = (
        (
            isinstance(pages, list)
            and len(pages) >= 2
            and all(type(p) is int and p > 0 for p in pages)
            and all(b == a + 1 for a, b in pairwise(pages))
        )
        if ranged
        else type(pages) is int and pages > 0
    )
    if (
        not isinstance(value, dict)
        or set(value) != {page_key, "printed_page_label", "later_hand_page_label"}
        or not valid_pages
        or any(
            item is not None
            and (not isinstance(item, str) or not re.fullmatch(r"[0-9A-Za-z?\[\] .—-]{1,64}", item))
            for item in (value["printed_page_label"], value["later_hand_page_label"])
        )
    ):
        raise ValueError("Invalid source page locator")
    result = dict(value)
    if ranged:
        result[page_key] = list(pages)
    return result
