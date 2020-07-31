# Virtual SDCard print stat tracking
#
# Copyright (C) 2020  Eric Callahan <arksine.code@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

class PrintStats:
    def __init__(self, config):
        printer = config.get_printer()
        self.gcode = printer.lookup_object('gcode')
        self.reactor = printer.get_reactor()
        self.reset()
    def _update_filament_usage(self, eventtime):
        gc_status = self.gcode.get_status(eventtime)
        cur_epos = gc_status['last_epos']
        self.filament_used += (cur_epos - self.last_epos) \
            / gc_status['extrude_factor']
        self.last_epos = cur_epos
    def set_current_file(self, filename):
        self.reset()
        self.filename = filename
    def note_start(self):
        curtime = self.reactor.monotonic()
        if self.print_start_time is None:
            self.print_start_time = curtime
        elif self.last_pause_time is not None:
            # Update pause time duration
            pause_duration = curtime - self.last_pause_time
            self.prev_pause_duration += pause_duration
            self.last_pause_time = None
        # Reset last e-position
        gc_status = self.gcode.get_status(curtime)
        self.last_epos = gc_status['last_epos']
    def note_pause(self):
        if self.last_pause_time is None:
            curtime = self.reactor.monotonic()
            self.last_pause_time = curtime
            # update filament usage
            self._update_filament_usage(curtime)
    def reset(self):
        self.filename = ""
        self.prev_pause_duration = self.last_epos = 0.
        self.filament_used = 0.
        self.print_start_time = self.last_pause_time = None
    def get_status(self, eventtime):
        total_duration = 0.
        time_paused = self.prev_pause_duration
        if self.print_start_time is not None:
            if self.last_pause_time is not None:
                # Calculate the total time spent paused during the print
                time_paused += eventtime - self.last_pause_time
            else:
                # Accumulate filament if not paused
                self._update_filament_usage(eventtime)
            total_duration = eventtime - self.print_start_time
        return {
            'filename': self.filename,
            'total_duration': total_duration,
            'print_duration': total_duration - time_paused,
            'filament_used': self.filament_used
        }

def load_config(config):
    return PrintStats(config)
