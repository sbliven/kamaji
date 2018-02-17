from .postfslint import ActionType
import os
import sys
import re

def rule_toprint(actions):
    """
    Keep duplicates if they have 'print' in the dirname
    """
    for action in actions:
        if action.type == ActionType.UNKNOWN:
            if 'print' in os.path.dirname(action.path).lower():
                action.type = ActionType.KEEP
    return True  # Keep going


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
defaultrules = (rule_toprint, rule_specificity, rule_single)

