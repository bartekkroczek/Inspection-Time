from .AbstractAdaptive import AbstractAdaptive


class NUpNDown(AbstractAdaptive):
    def __init__(self, n_up, n_down, max_revs, start_val, step_up=1, step_down=1):
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

        # Required positive parameters.
        assert all(x > 0 for x in [n_up, n_down, max_revs, step_up]), 'Illegal init value.'
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
        self.switch_in_last_trial_flag = False

    def __iter__(self):
        return self

    def __next__(self):
        # set_corr() must be called between iterations.
        if not self.set_corr_flag:
            raise Exception('NUpNDown.set_corr() must be called at least once per iteration.')
        self.set_corr_flag = False

        # Stop after the configured number of reversals.
        if self.revs_count < self.max_revs:
            return self.curr_val
        else:
            raise StopIteration()

    def set_corr(self, corr):
        """Report the correctness of the last iteration; may shift curr_val."""
        assert isinstance(corr, bool), 'Correctness must be a boolean value.'

        self.set_corr_flag = True
        self.switch_in_last_trial_flag = False
        jump = 0

        # Update the corresponding run-length counter; reset the other one.
        if corr:
            self.no_corr_in_a_row += 1
            self.no_incorr_in_a_row = 0
        else:
            self.no_corr_in_a_row = 0
            self.no_incorr_in_a_row += 1

        # Did we hit a step threshold?
        if self.n_up == self.no_corr_in_a_row:
            self.curr_val -= self.step_up
            jump = 1   # Moved UP the staircase (harder); curr_val decreased.

        if self.n_down == self.no_incorr_in_a_row:
            self.curr_val += self.step_down
            jump = -1  # Moved DOWN the staircase (easier); curr_val increased.

        # Was this jump a reversal?
        if jump:
            if not self.last_jump_dir:
                # First jump: remember the direction.
                self.last_jump_dir = jump
            elif jump != self.last_jump_dir:
                # Direction switched: count a reversal.
                self.revs_count += 1
                self.last_jump_dir = jump
                self.switch_in_last_trial_flag = True
            # Reset counters after the jump.
            self.no_incorr_in_a_row = 0
            self.no_corr_in_a_row = 0

    def get_jump_status(self):
        return self.last_jump_dir, self.switch_in_last_trial_flag, self.revs_count