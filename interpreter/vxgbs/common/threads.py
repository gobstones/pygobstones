#
# Copyright (C) 2011, 2012 Pablo Barenbaum <foones@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# # You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import common.utils

import multiprocessing
import threading

if common.utils.python_major_version() < 3:
    import Queue as queue
else:
    import queue

#### Workaround for Python issue 3770

try:
    multiprocessing.Queue()
    MULTIPROCESSING_ENABLED = True
except:
    MULTIPROCESSING_ENABLED = False
    sys.stderr.write('PyGobstones warning: multiprocessing disabled. See Python issue 3770\n')

if MULTIPROCESSING_ENABLED:

    Queue = multiprocessing.Queue

    Process = multiprocessing.Process
    Thread = threading.Thread
    
    def terminate_process(p):
        return p.terminate()

else:

    Queue = queue.Queue

    Process = threading.Thread

    def terminate_process(p):
        sys.stderr.write('PyGobstones warning: unable to terminate process. See Python issue 3770\n')

queue_empty = queue.Empty

