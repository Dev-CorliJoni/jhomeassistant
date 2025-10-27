from enum import StrEnum


class AvailabilityMode(StrEnum):
    """
    Defines how to derive availability when combining multiple inputs.

    - LATEST: Use the most recently updated source or snapshot when values conflict.
    - ALL:    Condition is true only if every input/source satisfies it (logical AND; set intersection).
    - ANY:    Condition is true if at least one input/source satisfies it (logical OR; set union).

    Guidance:
        Use ALL for strict consistency, ANY for higher coverage and fault tolerance,
        and LATEST when recency is the primary tiebreaker between conflicting values.
    """
    LATEST = "latest"  # Most recent source wins
    ALL = "all"        # All sources must agree
    ANY = "any"        # One agreeing source is enough
