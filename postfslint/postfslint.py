import re
import os
import sys
from collections import OrderedDict, UserList
import abc
from enum import Enum
import logging
import itertools
from distutils import spawn  # for find_executable
import subprocess


class ActionType(Enum):
    """Types of actions that can be performed"""

    KEEP = "K"
    DELETE = "D"
    RENAME = "R"
    UNKNOWN = "?"


# OS-specific delete function
if spawn.find_executable("trash"):
    def delete(path):
        logging.info("Trashing %s", path)
        result = subprocess.check_call(["trash", path], stdout=sys.stdout, stderr=sys.stderr)
        if result != 0:
            logging.error("Trashing {} returned {}", path, result)
        return True
else:
    def delete(path):
        logging.info("Deleting %s", path)
        os.remove(path)
        return True


def rename(src, dst):
    logging.info("Renaming %s to %s", src, dst)
    os.rename(src, dst)
    return True


class Action(object):
    """Encapsulates an action to be performed. Actions apply to a path and may take additional arguments."""

    def __init__(self, actiontype, path, *args):
        self.type = ActionType(actiontype)
        self.path = path
        self.args = args
        self.check_args()

    def check_args(self):
        """Check arguments for consistency

        Throws: (ValueError) upon inconsistencies

        """
        if not isinstance(self.type, ActionType):
            raise ValueError("Invalid ActionType")

        if self.path is None:
            raise ValueError("No path")

        if self.type is ActionType.RENAME:
            if self.args is None or len(self.args) != 1:
                raise ValueError("No destination for RENAME action")
        else:
            if self.args is not None and len(self.args) > 0:
                raise ValueError("Too many arguments for {} action".format(self.type))

    def __str__(self):
        return "\t".join([self.type.value, self.path] + list(self.args))

    # @classmethod
    # def to_yaml(cls, representer, node):
    #     representer.represent_yaml_object(cls.yaml_tag, new_data, cls,
    #                                         flow_style=cls.yaml_flow_style)

    @classmethod
    def from_tsv(cls, line):
        """Construct an Action from a tab-delimited line

        Throws (ValueError) for invalid formatting.

        """
        fields = line.split('\t')
        return Action(*fields)

    def apply(self, dryrun=False):
        """Apply action

        Return: (bool) whether the action was successful

        """
        if self.type in [ActionType.KEEP, ActionType.UNKNOWN]:
            # Ignore
            return

        # Test path exists
        if not os.path.isfile(self.path):
            raise IOError("Unable to %s '%s' (file not found)" % (self.type.name, self.path))
        if self.type is ActionType.DELETE:
            if dryrun:
                logging.info("Deleting %s", self.path)
            else:
                return delete(self.path)
        elif self.type is ActionType.RENAME:
            if dryrun:
                logging.info("Renaming %s to %s", self.path, self.args[0])
            else:
                return rename(self.path, self.args[0])
        else:
            raise Exception("Unimplemented Action")



class DupGroup(UserList):
    """Group of duplicate files"""

    def __init__(self, actions=None, paths=None):
        if actions is None and paths is None:
            raise ValueError("Requires either actions or paths argument")
        if actions is not None:
            super().__init__(actions)
        else:
            super().__init__(Action(ActionType.UNKNOWN, path) for path in paths)

    def annotate(self, rules):
        """Apply a set of rules to the actions
        Args:
            - rules (list of ([action] -> bool)): List of rules. Each rule is a callable
                accepting a list of actions, possibly modifying them, and
                returning a bool indicating whether additional rules should be
                applied.
        Returns: self, for chaining

        """
        for rule in rules:
            result = rule(self)
            if not result:
                break
        return self

    @property
    def annotation(self):
        """Helper property to get the type of each Action in this group

        Returns: list of ActionType

        """
        return [a.type for a in self]

    @property
    def paths(self):
        """Helper property to get the path for each Action in this group"""
        return [a.path for a in self]

    def __repr__(self):
        return "DupGroup({!r})".format(self)

    def __str__(self):
        return "\n".join(str(a) for a in self)

    def apply(self, dryrun=False):
        """Apply actions"""
        for action in self:
            allworked = True
            try:
                allworked = allworked and action.apply(dryrun)
            except Exception as ex:
                logging.error(ex)

class DupList(UserList):
    @staticmethod
    def parse_fslint(file):
        """
        Args:
            - file (file-like): fslint output file

        Returns: dict(section name -> list of lines)

        """
        lines = file.readlines()
        sections = OrderedDict()
        sectionname = None
        section = []
        for line in lines:
            match = re.match('-{5,}(.*)\n?', line)
            if match:
                # new section
                if section or sectionname:
                    sections[sectionname] = section
                sectionname = match.group(1)
                section = []
            else:
                section.append(line)
        if section or sectionname:
            sections[sectionname] = section
        return sections

    @staticmethod
    def fslint_duplist(sections):
        dupsection = "DUPlicate files"
        if dupsection not in sections:
            dupsection = None  # Fall back to top section
        dups = [DupGroup(paths=paths.split('\n')) for paths in "".join(sections[dupsection]).strip().split("\n\n")]
        return dups

    def __init__(self, fslint=None, tsv=None):
        """
        Args:
            - fslint (file-like): fslint output to parser
        """
        super().__init__()
        if fslint:
            self.read_fslint(fslint)
        if tsv:
            self.read_tsv(tsv)

    def read_fslint(self, fslint):
        sections = self.parse_fslint(fslint)
        self.extend(self.fslint_duplist(sections))

    def read_tsv(self, tsv):
        """Read a tsv action file.

        Groups are separated by blank lines, actions are tab-delimited newlines
        starting with the ActionType.

        Adds any actions read to this list.
        """
        # group by newlines
        dups = []
        actions = []
        for linenum, line in enumerate(tsv.readlines()):
            line = line.rstrip("\n")
            if line:
                if line[0] == "#":
                    continue
                # continue group
                try:
                    action = Action.from_tsv(line)
                    actions.append(action)
                except ValueError as ex:
                    logging.error("Parse error line {}: {}".format(linenum, ex))
            else:
                # start new group
                if actions:
                    dups.append(DupGroup(actions))
                actions = []
        if actions:
            dups.append(DupGroup(actions))

        self.extend(dups)

    def __str__(self):
        """TSV-formatted string"""
        return "\n\n".join(str(dup) for dup in self)

    def write(self, outfile):
        outfile.write("""# Actions:
# K\tsrc\t\tKeep the file
# D\tsrc\t\tDelete the file
# R\tsrc\tdst\tRename the file to `dst`
# ?\tsrc\t\tUnknown - keep file as is
""")
        outfile.write(str(self))

    def annotate(self, rules):
        for dup in self:
            dup.annotate(rules)

    def apply(self, dryrun=False):
        """Apply actions"""
        for dup in self:
            dup.apply(dryrun)


