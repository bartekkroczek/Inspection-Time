from .AbstractAdaptive import AbstractAdaptive


class NUpNDown(AbstractAdaptive):
    def __init__(self, n_up=3, n_down=1, max_revs=8, start_val=10, step_up=1, step_down=1):
        """
        Transformed up-down staircase. On each iteration the class yields
        **curr_val**, starting from **start_val**. The caller reports whether
        the participant was correct via set_corr(bool); the value then changes
        according to:

        * **n_up** correct answers in a row -> curr_val is **decreased** by
          **step_up** (the participant moves "up" the staircase, toward harder).
        * **n_down** incorrect answers in a row -> curr_val is **increased** by
          **step_down** (the participant moves "down" the staircase, toward
          easier).

        Naming convention is psychophysical: "up"/"down" refer to staircase
        difficulty, not to the direction of curr_val. A 2-down-1-up rule is
        therefore expressed as ``n_up=2, n_down=1`` here.

        Iteration terminates after **max_revs** reversals (direction switches
        between an n_up step and an n_down step).

        :param n_up: Correct answers in a row required to decrease curr_val.
        :param n_down: Incorrect answers in a row required to increase curr_val.
        :param max_revs: Number of reversals at which the staircase terminates.
        :param start_val: Initial value of curr_val.
        :param step_up: Amount curr_val is decreased by after n_up correct.
        :param step_down: Amount curr_val is increased by after n_down wrong.
        """

        # Some vals must be positive, check if that true.
        assert all(map(lambda x: x > 0, [n_up, n_down, max_revs, step_up])), 'Illegal init value'
        self.n_up = n_up
        self.n_down = n_down
        self.max_revs = max_revs
        self.curr_val = start_val
        self.step_up = step_up
        self.step_down = step_down

        self.no_corr_in_a_row = 0
        self.no_incorr_in_a_row = 0
        self.last_jump_dir = 0
        self.revs_count = 0
        self.set_corr_flag = True
        self.switch_in_last_trail_flag = False

    def __iter__(self):
        return self

    def __next__(self):
        # Set_corr wasn't used after last iteration. That's quite bad.
        if not self.set_corr_flag:
            raise Exception(" class.set_corr() must be used at least once "
                            "in any iteration!")
        self.set_corr_flag = False

        # check if it's time to stop alg.
        if self.revs_count < self.max_revs:
            return self.curr_val
        else:
            raise StopIteration()

    def set_corr(self, corr):
        """
        This func determine changes in value returned by next.

        :param **corr**: Correctness in last iteration.

        :return: None
        """
        # check if corr val make sense
        assert isinstance(corr, bool), 'Correctness must be a boolean value'

        self.set_corr_flag = True  # set_corr are used, set flag.
        self.switch_in_last_trail_flag = False
        jump = 0

        # increase no of corr or incorr ans in row.
        if corr:
            self.no_corr_in_a_row += 1
            self.no_incorr_in_a_row = 0
        else:
            self.no_corr_in_a_row = 0
            self.no_incorr_in_a_row += 1

        # check if it's time to change returned value
        if self.n_up == self.no_corr_in_a_row:
            self.curr_val -= self.step_up
            jump = 1   # moved UP the staircase (harder); curr_val decreased

        if self.n_down == self.no_incorr_in_a_row:
            self.curr_val += self.step_down
            jump = -1  # moved DOWN the staircase (easier); curr_val increased

        if jump:  # check if jump was also a switch
            if not self.last_jump_dir:
                # it was first jump, remember direction.
                self.last_jump_dir = jump
            elif jump != self.last_jump_dir:
                # yes, it was switch.
                self.revs_count += 1
                self.last_jump_dir = jump
                self.switch_in_last_trail_flag = True
            # clear counters after jump
            self.no_incorr_in_a_row = 0
            self.no_corr_in_a_row = 0

    def get_jump_status(self):
        return self.last_jump_dir, self.switch_in_last_trail_flag, self.revs_count