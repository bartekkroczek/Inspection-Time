from abc import ABCMeta, abstractmethod


class AbstractAdaptive(object):
    """
    Abstract class that defines API for all adaptive algorithms.
    All subclasses inhering from this class will be iterable.

    Usage:

    ```python
    for val in class:
        ... calculations with val...
        class.set_corr(...)
    ```

    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __iter__(self):
        pass

    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def set_corr(self, corr):
        pass


class NUpNDown(AbstractAdaptive):
    def __init__(self, n_up=3, n_down=1, max_revs=8, start_val=10, step=1):
        """
        This class will be returning some value in any iteration.
        At start it will be start_val.
        After n_up correct answers (set_corr(True))
        value will be increased by step.
        Analogically, after n_down * (set_corr(False)) value will be
        decreased by step.
        If swipe (change between series of up's of series of down's)
        will be detected max_revs times, algorithm will be terminated.

        :param n_up: No of set_corr(True) before inc value.
        :param n_down: No of set_corr(False) before dec value.
        :param max_revs: No of swipes before end of alg.
        :param start_val: Initial value
        :param step: Values of inc and dec with n_up and n_down.
        """

        # Some vals must be positive, check if that true.
        assert all(map(lambda x: x > 0, [n_up, n_down, max_revs, step])), 'Illegal init value'
        self.n_up = n_up
        self.n_down = n_down
        self.max_revs = max_revs
        self.curr_val = start_val
        self.step = step

        self.jumps = 0
        self.no_corr_in_a_row = 0
        self.no_incorr_in_a_row = 0
        self.last_jump_dir = 0
        self.revs_count = 0
        self.set_corr_flag = True

    def __iter__(self):
        return self

    def next(self):
        # Set_corr wasn't used after last iteration. That's quite bad.
        if not self.set_corr_flag:
            raise Exception(" class.set_corr() must be used at least once "
                            "in any iteration!")
        self.set_corr_flag = False

        # check if it's time to stop alg.
        if self.revs_count <= self.max_revs:
            return self.curr_val
        else:
            raise StopIteration()

    def set_corr(self, corr):
        """
        This func determine changes in value returned by next.
        :param corr: Correctness in last iteration.
        :return: None
        """
        # check if corr val make sense
        assert isinstance(corr, bool), 'Correctness must be a boolean value'

        self.set_corr_flag = True  # set_corr are used, set flag.
        jump = 0

        # increase no of corr or incorr ans in row.
        if corr:
            self.no_corr_in_a_row += 1
            self.no_incorr_in_a_row = 0
        else:
            self.no_incorr_in_a_row += 1
            self.no_corr_in_a_row = 0

        # check if it's time to change returned value
        if self.n_up == self.no_corr_in_a_row:
            jump = 1  # mean increase

        if self.n_down == self.no_incorr_in_a_row:
            jump = -1  # mean decrease

        if jump:
            self.curr_val = self.curr_val + jump * self.step
            # check if jump was also a switch
            if not self.last_jump_dir:
                # it was first jump, remember direction.
                self.last_jump_dir = jump
            elif jump != self.last_jump_dir:
                # yes, it was switch.
                self.revs_count += 1
                self.last_jump_dir = jump
            # clear counters after jump
            self.no_incorr_in_a_row = 0
            self.no_corr_in_a_row = 0


# Propositions of different adaptive algs.

class NUpNDownMaxIters(AbstractAdaptive):
    pass


class MaxIters(AbstractAdaptive):
    pass
