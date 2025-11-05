# Hotkey Engineer Plugins Bot_Helper - This is a wrapper script to execute your discord bot with Hotkey Engineer.
#
# Copyright (C) 2025 Eniti-Codes
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
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import subprocess
import os
import sys
import signal

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(SCRIPT_DIR, 'bot.pid')

# ----- Existing Configuration -----
VENV_FOLDER_NAME = "venv"
VENV_PYTHON_EXEC = os.path.join(SCRIPT_DIR, VENV_FOLDER_NAME, 'bin', 'python3')
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, 'main.py')
# ----------------------------------

# --- Helper Functions ---

def start_bot():
    """Starts the bot in the background and writes its PID to file."""
    if not os.path.exists(VENV_PYTHON_EXEC):
        print(f"ERROR: Venv Python not found at: {VENV_PYTHON_EXEC}")
        sys.exit(1)

    command = [VENV_PYTHON_EXEC, MAIN_SCRIPT] + sys.argv[1:]
    
    print(f"INFO: Starting bot with command: {' '.join(command)}")

    try:
        with open(os.devnull, 'w') as devnull:
            process = subprocess.Popen(
                command, 
                cwd=SCRIPT_DIR, 
                env=os.environ,
                stdout=devnull, 
                stderr=devnull,
                start_new_session=True
            )
        
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))
        
        print(f"SUCCESS: Bot started with PID {process.pid}. PID written to {PID_FILE}")
        sys.exit(0)
    except Exception as e:
        print(f"FATAL ERROR during bot startup: {e}")
        sys.exit(1)


def stop_bot():
    """Reads PID, sends a terminate signal, and deletes the PID file."""
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
    except FileNotFoundError:
        print("ERROR: PID file found, but could not read PID.")
        return False
    except ValueError:
        print("ERROR: PID file contains invalid content.")
        os.remove(PID_FILE)
        return False

    print(f"INFO: Attempting to stop process with PID {pid}...")
    
    try:
        os.kill(pid, signal.SIGTERM) 
        print(f"SUCCESS: Sent SIGTERM to process {pid}.")
        
        os.remove(PID_FILE)
        sys.exit(0)
        
    except ProcessLookupError:
        print(f"WARNING: Process with PID {pid} not found (already dead?). Cleaning up PID file.")
        os.remove(PID_FILE)
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Could not stop process {pid}: {e}")
        sys.exit(1)


# --- Main Toggle Logic ---

if os.path.exists(PID_FILE):
    print("DEBUG: PID file found. Attempting to stop bot.")
    stop_bot()
else:
    print("DEBUG: No PID file found. Attempting to start bot.")
    start_bot()