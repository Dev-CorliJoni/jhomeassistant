from enum import Enum


def resolve_abbreviation(value: Enum, abbreviated):
    first, second = value.value
    if abbreviated:
        return second
    else:
        return first
