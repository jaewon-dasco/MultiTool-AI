#coding: utf8
from __future__ import print_function

import sys, os, subprocess
from array import array

SIMULATION_SCRIPT="D:/4_AIProject/4_CoDeSys/AI_MutiTool/MultiToolProject/E2EProject/EPEC_CU4/project_update_simulation.py"
NORMAL_SCRIPT="D:/4_AIProject/4_CoDeSys/AI_MutiTool/MultiToolProject/E2EProject/EPEC_CU4/project_update.py"

def run_script_file(script_path):
    """
    Loads and executes a Python script file in the global context.
    
    :param script_path: Path to the Python script to execute.
    """
    try:
        with open(script_path, "r") as f:
            code = compile(f.read(), script_path, 'exec')
            exec(code, globals())
    except Exception as e:
        system.write_message(Severity.Error, "Error executing script " + script_path + ":" + str(e))

def is_simulation_device_in_use(project):
    """
    Checks if the device id is simulation device's ID
    """
    try:
        device = project.find("Device", True)[0]
        device_id = device.get_device_identification().id
        
        value = int(device_id.replace(" ", ""), 16)
        is_simulation = (value >> 15) & 1 == 1
        return is_simulation
    except Exception:
        system.write_message(Severity.Error, "Reading device id failed, default update script will be run") 
        return False

def main(project):
    if SIMULATION_SCRIPT != "" and is_simulation_device_in_use(project):
        run_script_file(SIMULATION_SCRIPT)
    else:
        run_script_file(NORMAL_SCRIPT)

if projects.primary:
    main(projects.primary)
