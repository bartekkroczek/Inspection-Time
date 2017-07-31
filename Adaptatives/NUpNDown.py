class NUpNDown(object):
    def __init__(self, n_up=3, n_down=1, max_revs=8, start_val=10, step=1):
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

    def get_next_val(self):
        if self.revs_count >= self.max_revs:
            return None
        else:
            return self.curr_val

    def is_finished(self):
        next_val = self.get_next_val()
        if next_val is None:
            return True
        else:
            return False

    def set_last_corr(self, correctness):
        jump = 0
        if correctness:
            self.no_corr_in_a_row += 1
            self.no_incorr_in_a_row = 0
        else:
            self.no_incorr_in_a_row += 1
            self.no_corr_in_a_row = 0

        if self.n_up == self.no_corr_in_a_row:
            self.curr_val += self.step
            self.no_corr_in_a_row = 0
            jump = 1
        if self.n_down == self.no_incorr_in_a_row:
            self.curr_val -= self.step
            self.no_incorr_in_a_row = 0
            jump = -1

        if jump:
            if not self.last_jump_dir:
                self.last_jump_dir = jump
            elif jump != self.last_jump_dir:
                self.revs_count += 1
                self.last_jump_dir = jump
