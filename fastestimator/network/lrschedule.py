import math

import numpy as np


class LRSchedule:
    def __init__(self, schedule_mode):
        self.schedule_mode = schedule_mode
        self.total_epochs = None  #will be filled by runtime
        self.total_steps = None  #will be filled by runtime
        self.initial_lr = None  #will be filled by runtime

    def schedule_fn(self, current_step_or_epoch, lr):
        #do something to change lr
        return lr


class CyclicLRSchedule(LRSchedule):
    def __init__(self, num_cycle=1, cycle_multiplier=2, decrease_method="cosine"):
        super().__init__(schedule_mode="step")
        self.num_cycle = num_cycle
        self.cycle_multiplier = cycle_multiplier
        self.decrease_method = decrease_method
        self.decay_fn_map = {"cosine": self.lr_cosine_decay, "linear": self.lr_linear_decay}
        assert self.cycle_multiplier >= 1, "The cycle_multiplier should at least be 1"

    def lr_linear_decay(self, current_step, lr_start, lr_end, step_start, step_end):
        slope = (lr_start - lr_end) / (step_start - step_end)
        intercept = lr_start - slope * step_start
        lr = slope * current_step + intercept
        return np.float32(lr)

    def lr_cosine_decay(self, current_step, lr_start, lr_end, step_start, step_end):
        current_step_in_cycle = (current_step - step_start) / (step_end - step_start)
        lr = (lr_start - lr_end) / 2 * math.cos(current_step_in_cycle * math.pi) + (lr_start + lr_end) / 2
        return np.float32(lr)

    def schedule_fn(self, current_step_or_epoch, lr):
        if self.cycle_multiplier == 1:
            total_unit_cycles = self.num_cycle
        else:
            total_unit_cycles = (self.cycle_multiplier**self.num_cycle - 1) / (self.cycle_multiplier - 1)
        unit_cycle_length = self.total_steps // total_unit_cycles
        step_start = 0
        for i in range(self.num_cycle):
            current_cycle_length = unit_cycle_length * self.cycle_multiplier**i
            if (current_step_or_epoch - step_start) < current_cycle_length:
                step_end = step_start + current_cycle_length
                break
            else:
                if i == (self.num_cycle - 1):
                    step_end = self.total_steps
                else:
                    step_start = step_start + current_cycle_length
        lr = self.decay_fn_map[self.decrease_method](current_step_or_epoch, self.initial_lr, 1e-6, step_start, step_end)
        return np.float32(lr)
