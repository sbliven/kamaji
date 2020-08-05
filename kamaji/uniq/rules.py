from .postfslint import ActionType
import os
import sys
import re


def rule_re(pattern, newtype=ActionType.KEEP, flags=re.I):
    """Marks files if any of their parent directories match a regular expression

    Args:
        - pattern (str): regular expression, matched against each directory in the action's path
        - newtype (ActionType): type to set upon matching (default: KEEP)
        - flags (int): regular expression flags (default: re.IGNORECASE)

    Returns: (list of Action -> bool)
        A rule function, which when evaluated on a list of rules KEEPs any paths matching the pattern

    """
    def rule(actions):
        # compile regular expression
        patt = pattern if hasattr('match', pattern) else re.compile(pattern, flags)

        for action in actions:
            if action.type == ActionType.UNKNOWN:
                for action in actions:
                    if action.type == ActionType.UNKNOWN and patt.search(action.path):
                        action.type = newtype
        return True
    return rule


def rule_specificity(actions):
    """
    If one duplicate is in the parent directory of another, keep the deeper one.
    """
    dirnames = [os.path.dirname(a.path) for a in actions]
    for i in range(len(actions) - 1):
        for j in range(i + 1, len(actions)):
            common = os.path.commonpath([dirnames[i], dirnames[j]])
            if dirnames[i] != dirnames[j]:
                if common == dirnames[i]:
                    if actions[i].type == ActionType.UNKNOWN:
                        actions[i].type = ActionType.DELETE
                    # if actions[j].type == ActionType.UNKNOWN:
                    #     actions[j].type = ActionType.KEEP
                elif common == dirnames[j]:
                    if actions[j].type == ActionType.UNKNOWN:
                        actions[j].type = ActionType.DELETE
                    # if actions[i].type == ActionType.UNKNOWN:
                    #     actions[i].type = ActionType.KEEP
    return True


def rule_single(actions):
    """Keep last UNKNOWN duplicate"""
    unknown = None
    for i in range(len(actions)):
        if actions[i].type == ActionType.UNKNOWN:
            if unknown is not None:
                # more than one UNKNOWN
                return True
            else:
                unknown = i
    if unknown is not None:
        # exactly one UNKNOWN
        actions[unknown].type = ActionType.KEEP
        return False  # Done annotating
    # Multiple unknowns
    return True


# All rules
defaultrules = (
        rule_re("print|phone|sdcard|rsync|iphoto"),
        rule_re("^Unsorted", ActionType.DELETE),
        rule_specificity,
        rule_single)
