from pedal.report.feedback import Feedback

__all__ = ['Report']


class Report:
    """
    A class for storing Feedback generated by Tools, along with any auxiliary
    data that the Tool might want to provide for other tools.

    Attributes:
        feedback (list of Feedback): The raw feedback generated for this Report
                                     so far.
        suppressions (list of tuple(str, str)): The categories and labels that
                                                have been suppressed so far.
        group (int or str): The label for the current group. Feedback given
            by a Tool will automatically receive the current `group`. This
            is used by the Source tool, for example, in order to group feedback
            by sections.
        group_names (dict[group:str]): A printable, student-facing name for the
            group. When a group needs to be rendered out to the user, this
            will override whatever label was going to be presented instead.
        group_order (sequence or callable or None): The mechanism to use to
            order groups. If a sequence, the order will be inferred based on
            the order of elements in the sequence. If a callable, the callable
            will be used as a key function for `sort`. If `None`, then defaults
            to the natural ordering of the groups. Defaults to `None`.
        hooks (dict[str: list[callable]): A dictionary mapping events to
            a list of callable functions. Tools can register functions on
            hooks to have them executed when the event is triggered by another
            tool. For example, the Assertions tool has hooks on the Source tool
            to trigger assertion resolutions before advancing to next sections.
        _results (dict of str => any): Maps tool names to their data. The
                                       namespace for a tool can be used to
                                       store whatever they want, but will
                                       probably be in a dictionary itself.
    """
    group_order = None

    def __init__(self):
        """
        Creates a new Report instance.
        """
        self.clear()

    def clear(self):
        self.feedback = []
        self.suppressions = {}
        self._results = {}
        self.group = None
        self.group_names = {}
        self.hooks = {}

    def set_success(self, group=None):
        """
        Creates Successful feedback for the user, indicating that the entire
        assignment is done.
        """
        if group is None:
            group = self.group
        self.feedback.append(Feedback('set_success', priority='positive',
                                      result=True, group=group))

    def give_partial(self, value, message=None, group=None):
        if value is None:
            return False
        if group is None:
            group = self.group
        self.feedback.append(Feedback('give_partial', performance=value,
                                      priority='positive',
                                      group=group,
                                      mistake=message))
        return True

    def hide_correctness(self):
        self.suppressions['success'] = []

    def explain(self, message, priority='medium', line=None, group=None,
                label='explain'):
        misconception = {'message': message}
        if line is not None:
            misconception['line'] = line
        if group is None:
            group = self.group
        self.attach(label, priority=priority, category='instructor',
                    group=group, misconception=misconception)

    def gently(self, message, line=None, group=None, label='explain'):
        self.explain(message, priority='student', line=line, group=group,
                     label=label)

    def guidance(self, message, line=None, group=None, label='guidance'):
        hint = {'message': message}
        if line is not None:
            hint['line'] = line
        if group is None:
            group = self.group
        self.attach(label, priority='instructions', category='instructions', group=group, hint=hint)

    def compliment(self, message, line=None, group=None, label='explain'):
        self.explain(message, priority='positive', line=line, group=group,
                     label=label)

    def attach(self, label, **kwargs):
        self.feedback.append(Feedback(label, **kwargs))

    def log(self, message):
        pass

    def debug(self, message):
        pass

    def suppress(self, category, label=True, where=True):
        """
        Args:
            category (str): The category of feedback to suppress.
            label (str): A specific label to match against and suppress.
            where (bool or group): Which group of report to localize the
                suppression to. If instead `True` is passed, the suppression
                occurs in every group globally.
                TODO: Currently, only global suppression is supported.
        """
        category = category.lower()
        if isinstance(label, str):
            label = label.lower()
        if category not in self.suppressions:
            self.suppressions[category] = []
        self.suppressions[category].append(label)

    def add_hook(self, event, function):
        """
        Register the `function` to be executed when the given `event` is
        triggered.
        
        Args:
            event (str): An event name. Multiple functions can be triggered for
                the same `event`. The format is as follows:
                    "pedal.module.function.extra"

                The `".extra"` component is optional to add further nuance, but
                the general idea is that you are referring to functions that,
                when called, should trigger other functions to be called first.
            function (callable): A callable function. This function should
                accept a keyword parameter named `report`, which will 
        """
        if event not in self.hooks:
            self.hooks[event] = []
        self.hooks[event].append(function)

    def execute_hooks(self, event):
        if event in self.hooks:
            for function in self.hooks[event]:
                function(report=self)

    def __getitem__(self, key):
        if key not in self._results:
            self._results[key] = {}
        return self._results[key]

    def __setitem__(self, key, value):
        self._results[key] = value

    def __contains__(self, key):
        return key in self._results