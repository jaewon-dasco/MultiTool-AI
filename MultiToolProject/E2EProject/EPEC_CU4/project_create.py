#coding: utf8
from __future__ import print_function

import sys, os, subprocess
from array import array

APPLICATION_GUID="639b491f-5557-464c-af91-1471bac9f549"
LIBRARY_MANAGER_GUID="adb5cb65-8e1d-4a00-b70a-375ea27582f3"
PLCOPEN_XML=u"D:\\4_AIProject\\4_CoDeSys\\AI_MutiTool\\MultiToolProject\\E2EProject\\EPEC_CU4\\EPEC_CU4.xml"
PROJECT=u"D:\\4_AIProject\\4_CoDeSys\\AI_MutiTool\\MultiToolProject\\E2EProject\\EPEC_CU4\\EPEC_CU4.project"
APPLICATIONERRORSENUM=u""
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
        print("Creating task to application")
        task_obj = task_configuration_obj.create_task(name)
        task_obj.pous.add(prg, "")
        task_obj.priority = "30"
        task_obj.interval_unit = "ms"
        task_obj.interval = "20"
        task_obj.kind_of_task = KindOfTask.Cyclic
        task_obj.watchdog.enabled = False
        return
    except Exception as ex:
        system.write_message(Severity.Error, "Error in creating new task")
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

MAPPED_IO_VARIABLES = []


def make_io_mapping(project):
    if len(MAPPED_IO_VARIABLES) == 0:
        print("No mapped IO variables available")
        return
    # set mapping    
    found = project.find('io_interface', True)  
    if found is None:
        return
    params = found[0].connectors[0].host_parameters    

    print("Number of parameters in io-connector  " + str(len(params)))    
    print("Before setting new mapping clear all old mappings for Safe_IoManager and NonSafe_IoManager")          
    if len(params) > 0:
        for param in params:      
            if not param.io_mapping is None:
                if not param.io_mapping.variable is None:
                    removeMapping = 0
                if not param.io_mapping.variable is None:
                    if "Application.S_Inputs.".upper() in param.io_mapping.variable.upper():
                        removeMapping = 1
                    if "Application.Inputs.".upper() in param.io_mapping.variable.upper():
                        removeMapping = 1
                    if "Application.S_Outputs.".upper() in param.io_mapping.variable.upper():
                        removeMapping = 1
                    if "Application.Outputs.".upper() in param.io_mapping.variable.upper():
                        removeMapping = 1                    
                    # check if mapping must remove
                    if removeMapping == 1:
                        param.io_mapping.variable = ''

                
        for mapping,parameter_id in MAPPED_IO_VARIABLES:
            for param in params:      
                if int(parameter_id) == param.id:
                    param.io_mapping.variable = mapping
            
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

if projects.primary:  
  projects.primary.close()

project = projects.create(PROJECT)

project.import_xml(reporter, u"D:\\4_AIProject\\4_CoDeSys\\AI_MutiTool\\MultiToolProject\\E2EProject\\EPEC_CU4\\EPEC_CU4_Application.xml", True)

device = project.find("Device", True)[0]
if device.is_device:
    device.update(4096, "10C8 0002", "2.1.0.7")
    device.enable()
    
app = find_object_by_type_from_project(projects.primary, APPLICATION_GUID)
remove_libraries(project)

if not app is None:    
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
                    
    if AZURE_IN_SEPARATE_TASK == "True":
        create_new_task(app, "AZURE_TASK", "AZURE_TASK_PRG")
    if GLOBE_IN_SEPARATE_TASK == "True":
        create_new_task(app, "GLOBE_TASK", "GLOBE_TASK_PRG")
else:
   system.write_message(Severity.Error, "Cannot find application from project tree") 

project.check_all_pool_objects()
project.clean_all()

make_io_mapping(project)

if APPLICATIONERRORSENUM != "":
    project.import_xml(reporter, APPLICATIONERRORSENUM, True)
        
project.save()

print("--- Create Script finished. ---")

# Self destruct
os.remove(sys.argv[0])