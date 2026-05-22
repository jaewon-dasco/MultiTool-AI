#coding: utf8
from __future__ import print_function

import sys, os, subprocess
from array import array

PLCOPEN_XML=u"D:\\4_AIProject\\4_CoDeSys\\AI_MutiTool\\MultiToolProject\\E2EProject\\EPEC_CU4\\EPEC_CU4_simulation.xml"
APPLICATION_GUID="639b491f-5557-464c-af91-1471bac9f549"
LIBRARY_MANAGER_GUID="adb5cb65-8e1d-4a00-b70a-375ea27582f3"
APPLICATIONERRORSENUM=u""
NEW_DEVICE_TARGET_ID="10C8 8002"
SAFETY_PLC_TYPE=4098
CHANGE_UNIT_SAFETYMAIN_XML=u""
CHANGE_UNIT_FASTPARAMETERS_XML=u""
CHANGE_UNIT_USERMRAM_XML=u"C:\\Program Files (x86)\\Epec\\MultiTool Creator 8.4\\Resources\\Config\\ProjectTemplates\\PLCopenTemplate_ChangeUnit_UserMRAM.xml"
AZURE_IN_SEPARATE_TASK=u"False"
GLOBE_IN_SEPARATE_TASK=u"False"
#CODESYS GVL attribute
QUALIFIED_ONLY_ATTRIBUTE = "{attribute 'qualified_only'}"
#ISOBUS scripts are executed when true
ISOBUS_IMPORT_IN_USE = 0
ISOBUS_IMPORT_VT_XML = 0
ISOBUS_IMPORT_TC_XML = 0
#absolute path to ISOBUS python folder
ISOBUS_PYTHON_FOLDER_NAME = u""
#relative path and filename in python folder
ISOBUS_IOP_FILENAME = u""
#flash location attribute to GVL
ISOBUS_IOP_FLASH_LOCATION_ATTRIBUTE = ""
#object pool maximum size
ISOBUS_IOP_MAX_SIZE = 0 
SAFETY_TASK_WATCHDOG_ENABLED = False

LIBRARIES=[
    ('6000BootApplication', 'EPEC_6000BootApp', '3.5.6.0', 'Epec Oy'),
    ('6000BackLightControl', 'EPEC_6000BKL', '3.5.6.1', 'Epec Oy'),
    ('6107Int', 'EPEC_6000INT', '3.2.4.1', 'Epec Oy'),
    ('6000IoDrv', 'EPEC_6000IODRV', '3.5.16.2', 'Epec Oy'),
    ('6000UsbDrive', 'EPEC_6000USB', '3.5.6.0', 'Epec Oy'),
    ('6000MRAM', 'EPEC_6000MRAM', '3.5.6.4', 'Epec Oy'),
    ('6000Multimedia', 'EPEC_6000Multimedia', '3.5.13.1', 'Epec Oy'),
    ('6000SystemParameters', 'EPEC_6000SPRM', '3.5.13.1', 'Epec Oy'),
    ('6000SocketCAN', 'EPEC_6000SocketCAN', '3.5.13.0', 'Epec Oy'),
    ('6000CANVXD', 'EPEC_6000CANVXD', '1.0.0.3', 'Epec Oy'),
    ('AD Conversion', 'EPEC_ADC', '3.0.2.5', 'Epec Oy'),
    ('Analog Input', 'EPEC_AI', '3.0.0.5', 'Epec Oy'),
    ('CANL2 CANVXD', 'EPEC_CANL2', '4.0.0.2', 'Epec Oy'),
    ('CANopen', 'EPEC_CANopen', '4.0.14.1', 'Epec Oy'),
    ('CANopen OD Save', 'EPEC_ODSave', '4.1.1.3', 'Epec Oy'),
    ('CANVXD API', 'EPEC_CANVXD', '4.0.0.1', 'Epec Oy'),
    ('CSV Parser', 'EPEC_CSVParser', '3.1.1.3', 'Epec Oy'),
    ('Digital Output Diagnostic', 'EPEC_DOD', '3.1.0.0', 'Epec Oy'),
    ('Event Log GUI', 'EPEC_ELG', '3.0.1.9', 'Epec Oy'),
    ('Event Log Transfer', 'EPEC_ELT', '3.0.5.0', 'Epec Oy'),
    ('J1939 To Event Translator', 'EPEC_J1939Event', '3.0.2.2', 'Epec Oy'),
    ('Filters', 'EPEC_Filters', '3.0.1.4', 'Epec Oy'),
    ('SAE J1939', 'EPEC_J1939', '3.1.2.0', 'Epec Oy'),
    ('Application SDO Parameters', 'EPEC_PAR', '4.1.3.0', 'Epec Oy'),
    ('Software Download', 'EPEC_SWD', '4.1.4.3', 'Epec Oy'),
    ('Sensor Calibration And Diagnostic', 'EPEC_SCD', '3.0.1.6', 'Epec Oy'),
    ('Joystick Calibration And Diagnostic', 'EPEC_JCD', '3.2.0.6', 'Epec Oy'),
    ('Serial', 'EPEC_Serial', '3.5.6.0', 'Epec Oy'),
    ('GPS', 'EPEC_GPS', '3.2.0.1', 'Epec Oy'),
    ('OS Library', 'EPEC_OSLIB', '3.5.6.1', 'Epec Oy'),
    ('Modem', 'EPEC_Modem', '3.1.1.1', 'Epec Oy'),
    ('GlobE', 'EPEC_GLOBE', '1.3.0.0', 'Epec Oy'),
    ('WLAN', 'EPEC_WLAN', '1.2.0.1', 'Epec Oy'),
    ('GatE', 'EPEC_GatE', '1.0.2.6', 'Epec Oy'),
    ('Parameter Handler', 'EPEC_PH', '1.0.3.1', 'Epec Oy'),
    ('Modem Utility', 'EPEC_ModemUtil', '1.1.0.3', 'Epec Oy'),
    ('AddressClaiming', 'EPEC_ACL', '1.0.1.0', 'Epec Oy'),
    ('Azure', 'EPEC_AZURE', '1.1.2.0', 'Epec Oy'),
    ('Utility', 'EPEC_UTIL', '1.0.0.10', 'Epec Oy'),
    ('Datalogger', 'EPEC_DLOG', '1.0.0.0', 'Epec Oy'),
    ('J1939DM', 'EPEC_J1939DM', '1.0.0.3', 'Epec Oy'),
    ('MachineType', 'EPEC_MachineType', '1.0.0.2', 'Epec Oy'),
    ('DataTransfer', 'EPEC_DT', '3.0.4.0', 'Epec Oy'),
    ('IO Diagnostic', 'EPEC_IOD', '1.0.0.5', 'Epec Oy'),
    ('IO Diagnostic Transfer', 'EPEC_IODT', '1.0.0.2', 'Epec Oy'),
    ('Event Log', 'EPEC_EL', '3.3.4.0', 'Epec Oy')]

def find_libman(project):
    libraryManager = find_object_by_type_from_project(project, LIBRARY_MANAGER_GUID)
    if not libraryManager:
        return None
    if not libraryManager.is_libman:
        return None
    return libraryManager

def remove_library_manager(project):    
    libman = find_libman(project)
    if not libman:
        system.write_message(Severity.Error, "Cannot find library manager") 
        return

    try:
        libman.remove()
    except Exception as ex:
        system.write_message(Severity.Error, "Error in removing library manager")
        return

def remove_libraries(project):
    
    libman = find_libman(project)
    if not libman:
        system.write_message(Severity.Error, "Cannot find library manager") 
        return
    
    libReferences = libman.references
       
    removables = []        
        
    for libRef in libReferences:
        for libName, placeholder, version, company in LIBRARIES:
            placeholder_with_dash = "#" + placeholder

            # Remove all matching libraries
            # Library parameters are set in MT UI and exported to project at project update
            if placeholder_with_dash == libRef.name:
                removables.append(libRef.name)
                break

    for removable in removables:
        print("Removing library: ", removable)
        try:
            libman.remove_library(removable)
        except Exception as ex:
            print("Error in removing library ", removable, ":", ex)
            continue

def remove_libary(project, lib_placeholder):
    libman = find_libman(project)
    if not libman:
        system.write_message(Severity.Error, "Cannot find library manager") 
        return
    
    libReferences = libman.references
       
    placeholder_with_dash = "#" + lib_placeholder
    for libRef in libReferences:
        if placeholder_with_dash == libRef.name:
            libman.remove_library(libRef.name)
            break

def find_object_by_type_from_project(project, type):
    for obj in project.get_children():
        if str(obj.type).lower() == str(type).lower():
            return obj
        result = find_object_by_type(obj, type)
        if not result is None:
            return result
    return None         

def find_object_by_type(parent, type):
    if str(parent.type) == type:
        return parent
    for obj in parent.get_children():
        if str(obj.type).lower() == str(type).lower():
            return obj
        result = find_object_by_type(obj, type)
        if not result is None:
            return result
    return None   

def remove_code_template_folder(app):
    code_template_folder = None
    
    for obj in app.get_children(False):
        if not obj:
            return
        elif obj.is_folder:
            folder_name = obj.get_name(False)
            if folder_name == "CodeTemplate":
                print("CodeTemplate folder found")
                code_template_folder = obj
                break
        else:
            continue
    
    if not code_template_folder is None:
        try:
            print("Clearing CodeTemplate folder contents")
            code_template_folder.remove()
            return
        except Exception as ex:
            system.write_message(Severity.Error, "Error in clearing code template folder")
            return
    else:
        print("Application's code template folder is not found")
        return
        
def remove_safety_task(app):
    safety_task_obj = None
    for obj in app.get_children(True):
        if not obj:
            return
        elif obj.is_task:
            task_name = obj.get_name(False)
            if task_name == "SafePRG_TASK":
                safety_task_obj = obj
                break
            else:
                continue
        else:
            continue
    
    if not safety_task_obj is None:
        try:
            print("Removing safety task from application")
            safety_task_obj.remove()
            return
        except Exception as ex:
            system.write_message(Severity.Error, "Error in removing safety task")
            return
    else:
        print("Safety task was not found from application")
        return

# Creates default safety task when nonsafety unit is changed to safety unit
def create_safety_task(app):
    task_configuration_obj = None
    for obj in app.get_children(True):
        if not obj:
            return
        elif obj.is_task_configuration:
            task_configuration_obj = obj
            break
        else:
            continue
            
    if task_configuration_obj is None:
        print("Task configuration not found")
        return

    try:
        print("Creating safety task to application")
        safety_task_obj = task_configuration_obj.create_task("SafePRG_TASK")
        safety_task_obj.pous.add("S_PLC_PRG", "")
        safety_task_obj.priority = "0"
        safety_task_obj.interval_unit = "ms"
        safety_task_obj.interval = "10"
        safety_task_obj.kind_of_task = KindOfTask.Cyclic
        safety_task_obj.watchdog.enabled = True
        safety_task_obj.watchdog.time_unit = "ms"
        safety_task_obj.watchdog.time = "10"
        safety_task_obj.watchdog.sensitivity = "1"
        return
    except Exception as ex:
        system.write_message(Severity.Error, "Error in creating safety task")
        return

# Reads object pool binary file and imports data to existing CODESYS GVL
def isobus_import_object_pool(app, filename, gvl_name, object_pool_max_size, bytes_per_line):
    code_template_folder = None
    isobus_pool_obj = None
    print("Importing ISOBUS object pool")

    for obj in app.get_children(False):
        if not obj:
            return
        elif obj.is_folder:
            folder_name = obj.get_name(False)
            if folder_name == "CodeTemplate":
                code_template_folder = obj
                break
        else:
            continue

    if not code_template_folder is None:
        for obj in code_template_folder.get_children(True):
            if not obj:
                return
            else:
                obj_name = obj.get_name(False)
                if obj_name == gvl_name:
                    isobus_pool_obj = obj
                    break
    else:
        print("Application's code template folder is not found")
        

    if not isobus_pool_obj is None:
        try:
            file_handle = open (filename, "rb")
            pool_array_data = array("B")
            pool_array_data.fromstring(file_handle.read())
            file_handle.close()
            pool_size = len(pool_array_data)
            print("ISOBUS object pool size: " + str(pool_size))

            if isobus_pool_obj.textual_declaration.linecount > 0:
                # Clear GVL
                isobus_pool_obj.textual_declaration.remove(offset=0, length=isobus_pool_obj.textual_declaration.length)
            isobus_pool_obj.textual_declaration.append(QUALIFIED_ONLY_ATTRIBUTE + "\n")
            # Add location attribute only if defined
            if ISOBUS_IOP_FLASH_LOCATION_ATTRIBUTE != "":
                isobus_pool_obj.textual_declaration.append(ISOBUS_IOP_FLASH_LOCATION_ATTRIBUTE + "\n")
            isobus_pool_obj.textual_declaration.append("VAR_GLOBAL CONSTANT\n")
            isobus_pool_obj.textual_declaration.append("\tMAX_SIZE: DWORD := " + str(object_pool_max_size) + ";\n")
            # Check object pool size
            if pool_size == 0:
                isobus_pool_obj.textual_declaration.append("\tDATA: ARRAY [1..MAX_SIZE] OF BYTE;\n")
                isobus_pool_obj.textual_declaration.append("END_VAR\n")
            elif pool_size > object_pool_max_size:
                system.write_message(Severity.Error, "ISOBUS object pool data is too large")
                isobus_pool_obj.textual_declaration.append("\tDATA: ARRAY [1..MAX_SIZE] OF BYTE;\n")
                isobus_pool_obj.textual_declaration.append("END_VAR\n")
            else:
                # create array variable to GVL
                isobus_pool_obj.textual_declaration.append("\tDATA: ARRAY [1..MAX_SIZE] OF BYTE :=\n")
                isobus_pool_obj.textual_declaration.append("\t[\n")
                isobus_pool_obj.textual_declaration.append("\t\t")
                str_array_data = ""
                # Read binary data to temp string, appending to GVL directly is too slow
                for i in range(0, pool_size):
                    # Convert value to hex string and replace with CODESYS prefix
                    pool_value = "{:#04X}".format(pool_array_data[i]).replace("0X","16#")
                    # Add value to string
                    str_array_data = str_array_data + pool_value
                    # check if bytes left
                    if i < (pool_size-1):
                        str_array_data = str_array_data + ","
                        # change line
                        if i != 0 and (i+1) % bytes_per_line == 0:
                            str_array_data = str_array_data + "\n\t\t"
                # add data to GVL
                isobus_pool_obj.textual_declaration.append(str_array_data)
                #close array initialization
                isobus_pool_obj.textual_declaration.append("\n\t];\n")
                isobus_pool_obj.textual_declaration.append("END_VAR\n")

        except Exception as ex:
            system.write_message(Severity.Error, "Object pool handling error: " + str(ex))
    else:
        print("ISOBUS object pool GVL is not found")

    return
    
# Creates new default task 
def create_new_task(app, name, prg):
    task_configuration_obj = None
    for obj in app.get_children(True):
        if not obj:
            return
        elif obj.is_task_configuration:
            task_configuration_obj = obj
            break
        else:
            continue
            
    if task_configuration_obj is None:
        print("Task configuration not found")
        return

    try:
        taskExist = task_exist_by_name(app, name)
        if not taskExist:
            print("Creating task to application")
            task_obj = task_configuration_obj.create_task(name)
            task_obj.pous.add(prg, "")
            task_obj.priority = "30"
            task_obj.interval_unit = "ms"
            task_obj.interval = "20"
            task_obj.kind_of_task = KindOfTask.Cyclic
            task_obj.watchdog.enabled = False
        else:
            print("Task was allready found")
        return
    except Exception as ex:
        system.write_message(Severity.Error, "Error in creating safety task: {}".format(ex))
        return

def task_exist_by_name(app, name):
    task_found = False
    for obj in app.get_children(True):
        if not obj:
            return
        elif obj.is_task:
            task_name = obj.get_name(False)
            if task_name == name:
                task_found = True
                break
            else:
                continue
        else:
            continue
    return task_found

def remove_task(app, name):
    task_obj = None
    for obj in app.get_children(True):
        if not obj:
            return
        elif obj.is_task:
            task_name = obj.get_name(False)
            if task_name == name:
                task_obj = obj
                break
            else:
                continue
        else:
            continue
    
    if not task_obj is None:
        try:
            print("Removing task from application")
            task_obj.remove()
            return
        except Exception as ex:
            system.write_message(Severity.Error, "Error in removing task: {}".format(ex))
            return
    else:
        return

def update_safety_task_watchdog(app):
    for obj in app.get_children(True):
        if not obj:
            return
        elif obj.is_task:
            task_name = obj.get_name(False)
            if task_name == "SafePRG_TASK":
                obj.watchdog.enabled = SAFETY_TASK_WATCHDOG_ENABLED
                break
            else:
                continue
        else:
            continue
    
    return
    
MAPPED_IO_VARIABLES = []

def make_io_mapping(project):
    if len(MAPPED_IO_VARIABLES) == 0:
        print("No mapped IO variables available")
        return
    # Converts the MAPPED_IO_VARIABLES to following dictionary:
    # dictionary[ID] = VARIABLE
    mtc_io_mappings_dict = {id: mapping for mapping, id in MAPPED_IO_VARIABLES}
    
    # Loads io mappings from CODESYS
    found = project.find('io_interface', True) 
    params = found[0].connectors[0].host_parameters
    keywords = ["Application.S_Inputs.", "Application.Inputs.", "Application.S_Outputs.", "Application.Outputs."]
    if params:
        for param in params:
            codesys_io_mapping = param.io_mapping
            if codesys_io_mapping:
                # Checks if codesys IO mapping is still used in MTC
                mtc_io_mapping = mtc_io_mappings_dict.get(param.id)
                # If io_mapping is used in MTC, and it differs from current value, we overwrite it with MTC value
                if mtc_io_mapping and mtc_io_mapping != codesys_io_mapping.variable:
                    codesys_io_mapping.variable = mtc_io_mapping
                # If io_mapping is not used in MTC anymore and user hasn't modified the mapping in codesys, we clear it
                elif not mtc_io_mapping and codesys_io_mapping.variable and any(keyword.upper() in param.io_mapping.variable.upper() for keyword in keywords):
                    codesys_io_mapping.variable = ""
            
    else:
        print("Parameter list is null")


class Reporter(ImportReporter):
    def error(self, message):
        system.write_message(Severity.Error, message)

    def warning(self, message):
        system.write_message(Severity.Warning, message)

    def resolve_conflict(self, obj):
        print("resolved: ", obj)
        return ConflictResolve.Replace

    def added(self, obj):
        print("added: ", obj)

    def replaced(self, obj):
        print("replaced: ", obj)

    def skipped(self, obj):
        print("skipped: ", obj)

    @property
    def aborting(self):
        return False

reporter = Reporter()

def main(project):

    project_path = os.path.dirname(project.path)
    script_path = os.path.dirname(os.path.abspath(__file__))
    
    # Project path is not the same as script path
    # Verify from user that it is OK to continue
    if project_path != script_path:
        errorMessage = "Script path is not the same as project path!\n\nCurrent CODESYS project folder:%s\n\nUpdate script folder:%s\n\nContinue anyway?" % (project_path, script_path)
        if system.ui_present:
            result = system.ui.prompt(errorMessage, PromptChoice.YesNo, PromptResult.No)
            if result == PromptResult.No:
                return
        else:
            system.write_message(Severity.Error, "Script path is not the same as project path!") 
            return
            
    # Find application node from project tree
    app = find_object_by_type_from_project(project, APPLICATION_GUID)
    
    # Update device
    device = project.find("Device", True)[0]
    device_has_changed = False
    device_changed_simulation = False
    old_device_is_safety = False
    
    if device.is_device:
        current_device_id = device.get_device_identification()
        # Check if current device is safety PLC before possible target change
        if current_device_id.type == SAFETY_PLC_TYPE:
            old_device_is_safety = True
        # If device has been changed, remove library manager to avoid unused libraries when unit type has been changed
        if current_device_id.id != NEW_DEVICE_TARGET_ID:
            diff_in_devices = [(ord(a) ^ ord(b)) for a,b in zip(current_device_id.id, NEW_DEVICE_TARGET_ID)]
            allowed_diff = [0,0,0,0,0,8,0,0,0]
            if allowed_diff != diff_in_devices:
                device_has_changed = True
                print("Device type has changed")
                print("Removing library manager")
                remove_library_manager(project)
            else:
                device_changed_simulation = True
                print("ID changed between simulation and normal ID")
            
            # We need to remove EPEC_SA library before updating to generic device,
            # otherwise codesys will throw an error
            remove_libary(project, "EPEC_SA")
            
            # When device type is changed, update first to generic device to remove all unnecessary device connectors
            print("Change to generic device before updating to new target device")
            device.update(4096, "10C8 FFFF", "1.0.0.0")
        
        device.update(4096, "10C8 8002", "2.1.0.7")
    
    # Remove libraries AFTER device update, otherwise library parameters won't update
    # Remove existing libraries, this is needed to e.g. update library parameters
    remove_libraries(project)
    
    if APPLICATIONERRORSENUM != "":
        project.import_xml(reporter, APPLICATIONERRORSENUM, True)
        
    if not app is None:
        # Clear code template folder before updating code template contents, this removes components which are no longer in user
        remove_code_template_folder(app)
        # Import PLCopen xml into project
        app.import_xml(reporter, PLCOPEN_XML, True)
        if ISOBUS_IMPORT_IN_USE:
            isobus_bat = ISOBUS_PYTHON_FOLDER_NAME + "makeIsobus.bat"
            # hide command prompt window when bat file is executed
            startupinfo = None
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            try:
                print("Starting ISOBUS bat script")
                p = subprocess.Popen(isobus_bat, startupinfo=startupinfo)
                stdout, stderr = p.communicate()
                # check bat file return code
                if p.returncode == 0:
                    print("ISOBUS bat executed successfully")
                    # import object pool to CODESYS
                    isobus_import_object_pool(app, ISOBUS_PYTHON_FOLDER_NAME + ISOBUS_IOP_FILENAME, "G_ISOBUS_ObjectPool", ISOBUS_IOP_MAX_SIZE, 64)
                else:
                    system.write_message(Severity.Error, "ISOBUS bat returned error. See Python folder log files for more information.")
            except Exception as ex:
                system.write_message(Severity.Error, "Error in executing ISOBUS bat file: " + str(ex))
            # Language PLCopen XML import
            if ISOBUS_IMPORT_VT_XML or ISOBUS_IMPORT_TC_XML:
                try:
                    print("Importing generated Language PLCopen XML")
                    LANG_PLCOPEN_XML = ISOBUS_PYTHON_FOLDER_NAME + "Languages\\PLCopen_Language.xml"
                    app.import_xml(reporter, LANG_PLCOPEN_XML, True)
                except Exception as ex:
                    system.write_message(Severity.Error, "Error in importing Language PLCopen XML: " + str(ex))
            # VT PLCopen XML import
            if ISOBUS_IMPORT_VT_XML:
                try:
                    print("Importing generated VT PLCopen XML")
                    VT_PLCOPEN_XML = ISOBUS_PYTHON_FOLDER_NAME + "IsobusVt\\PLCopen_VT.xml"
                    app.import_xml(reporter, VT_PLCOPEN_XML, True)
                except Exception as ex:
                    system.write_message(Severity.Error, "Error in importing VT PLCopen XML: " + str(ex))
            # TC PLCopen XML import
            if ISOBUS_IMPORT_TC_XML:
                try:
                    print("Importing generated TC PLCopen XML")
                    TC_PLCOPEN_XML = ISOBUS_PYTHON_FOLDER_NAME + "IsobusTc\\PLCopen_TC.xml"
                    app.import_xml(reporter, TC_PLCOPEN_XML, True)
                except Exception as ex:
                    system.write_message(Severity.Error, "Error in importing TC PLCopen XML: " + str(ex))
                    
        # If unit has been changed in MultiTool, import additional components to project accordingly
        if device_has_changed:
            print("Checking missing or unnecessary components after device type change")
            current_device_id = device.get_device_identification()
            #If device was safety PLC before change and new device is not safety -> remove safety task
            if old_device_is_safety and current_device_id.type != SAFETY_PLC_TYPE:
                remove_safety_task(app)
            elif not old_device_is_safety and current_device_id.type == SAFETY_PLC_TYPE:
                create_safety_task(app)
            #Re-enable application I/O handling
            #This setting is reset when original device is updated to generic device before updating to new actual device
            device.driver_info.set_io_application(app)
            if CHANGE_UNIT_SAFETYMAIN_XML != "":
                safety_main_found = project.find("S_Main", True)
                if not safety_main_found:
                    print("Import Safety main POU XML")
                    app.import_xml(reporter, CHANGE_UNIT_SAFETYMAIN_XML, True)
            if CHANGE_UNIT_FASTPARAMETERS_XML != "":
                fastparameters_found = project.find("FastParameters", True)
                if not fastparameters_found:
                    print("Import fast parameters struct XML")
                    app.import_xml(reporter, CHANGE_UNIT_FASTPARAMETERS_XML, True)
            if CHANGE_UNIT_USERMRAM_XML != "":
                userMRAM_found = project.find("UserMRAMStructure", True)
                if not userMRAM_found:
                    print("Import user MRAM struct XML")
                    app.import_xml(reporter, CHANGE_UNIT_USERMRAM_XML, True)
        if device_changed_simulation:
            #Re-enable application I/O handling
            #This setting is reset when original device is updated to generic device before updating to new actual device
            device.driver_info.set_io_application(app)
        if AZURE_IN_SEPARATE_TASK == "True":
            create_new_task(app, "AZURE_TASK", "AZURE_TASK_PRG")
        else:
            remove_task(app, "AZURE_TASK")
        if GLOBE_IN_SEPARATE_TASK == "True":
            create_new_task(app, "GLOBE_TASK", "GLOBE_TASK_PRG")
        else:
            remove_task(app, "GLOBE_TASK")
            
        update_safety_task_watchdog(app)
    else:
        system.write_message(Severity.Error, "Cannot find application from project tree") 
    
    make_io_mapping(project)
    #  Finally save th project if everything went OK
    project.save()
    
    
if projects.primary:
    main(projects.primary)

print("--- Update Script finished. ---")