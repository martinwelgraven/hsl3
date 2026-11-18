
from datetime import datetime
import os

from hsl3.hsl3_generator.configs.dcls_module import ConfigModule
from hsl3.hsl3_generator.parsers.html import HTMLfileParser
from hsl3.hsl3_generator.parsers.module import ModuleParser
from hsl3.hsl3_generator.parsers.tests import TestfileParser
from hsl3.hsl3_generator.parsers.yaml import YAMLfileParser

from .json import JSONfileParser
from .python import PythonfileParser
from hsl3.hsl3_generator.configs.dcls_project import ConfigProject


class ProjectParser:
    
    def __init__(self, config: ConfigProject, action: str):
        self.project_config = config
        self.node_config: ConfigModule = ConfigModule(id=self.project_config.id, name=self.project_config.name) 
        
        if action == 'new':
            self._new()
        
        if action == "build":
            self._build()

    def _new(self):
        write_config = True
        if self.project_config.state == 'load':
            user_input = input(f"A project configuration exists. Do you want to load the existing configuration? (Y/N):")
            while user_input.lower() not in ['y', 'n']:
                user_input = input("Invalid input. Please enter 'Y' or 'N':")
            
            if user_input.lower() == 'y':
                self._load_config()
                write_config = False
            else:
                self.request_input()
        else:
            self.request_input()
        
        self.project_config.title = self.node_config.title
        self.project_config.category = self.node_config.category
        self.project_config.context = self.node_config.context
        
        if write_config:
            user_input = input(f"The JSON will now be written. Want to continue? (Y/N):")
            while user_input.lower() not in ['y', 'n']:
                user_input = input("Invalid input. Please enter 'Y' or 'N':")
            
            if user_input.lower() == 'y':
                if self.project_config.json_file:
                    JSONfileParser().write_first_json(self.project_config)
                elif self.project_config.yaml_file:
                    YAMLfileParser().write_first_yaml(self.project_config)
                else:
                    raise ValueError("No valid configuration file specified.")

        python_file = os.path.join(self.project_config.source_path, self.project_config.python_file)
        if os.path.exists(python_file):
            user_input = input(f"Do you want to overwrite the existing Python file? (Y/N):")
            while user_input.lower() not in ['y', 'n']:
                user_input = input("Invalid input. Please enter 'Y' or 'N':")
            if user_input.lower() == 'y':
                PythonfileParser().write_first_python(python_file, self.node_config)
        else:
            PythonfileParser().write_first_python(python_file, self.node_config)

        user_input = input(f"Would you like to create a test file? (Y/N):")
        while user_input.lower() not in ['y', 'n']:
            user_input = input("Invalid input. Please enter 'Y' or 'N':")
        if user_input.lower() == 'y':
            TestfileParser(self.project_config.root, self.project_config.json_file, self.node_config)
        
        
    def _build(self):
        self._load_config()
        self._versioning()
        self._build_hsl3()
        self._build_html()


    def _versioning(self):
        user_input = input(f"Do you want to update a version? (1 = major, 2 = minor or 3 = patch):")
        while user_input not in ['1', '2', '3']:
            user_input = input("Invalid input. Please enter '1', '2' or '3':")
        new_version = self.node_config.version.split('.')
        if user_input == '1':
            new_version[0] = str(int(new_version[0]) + 1)
            new_version[1] = '0'
            new_version[2] = '0'
        elif user_input == '2':
            new_version[1] = str(int(new_version[1]) + 1)
            new_version[2] = '0'
        elif user_input == '3':
            new_version[2] = str(int(new_version[2]) + 1)
        else:
            return

        self.node_config.version = '.'.join(new_version)
        self.node_config.version_date = datetime.now().strftime("%Y-%m-%d")

        user_input = input(f"Do you want to provide release notes for version {'.'.join(new_version)}? (Y/N):")
        while user_input.lower() not in ['y', 'n']:
            user_input = input("Invalid input. Please enter 'Y' or 'N':")
        note = None
        if user_input.lower() == 'y':
            note_add = input("Enter a short release note: ")
            if self.project_config.yaml_file and not self.project_config.json_file:
                previous_note = YAMLfileParser().read_note(self.project_config)
                note = (previous_note + '\n' + self.node_config.version + ' ' + note_add).replace('\\n', '\n')
                self.node_config.note = note.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')
            else:
                note = self.node_config.note + '\n' + self.node_config.version + ' ' + note_add
                self.node_config.note = note.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')

        if self.project_config.json_file:
            JSONfileParser().update_version(
                self.project_config, self.node_config.version, self.node_config.version_date, note
            )
        elif self.project_config.yaml_file:
            YAMLfileParser().update_version(
                self.project_config, self.node_config.version, self.node_config.version_date, note
            )
        else:
            raise ValueError("No configuration file found. Please provide a JSON or YAML configuration file.")
        

    def _build_hsl3(self):
        user_input = input(f"Do you want to build the HSL3 file? (Y/N):")
        while user_input.lower() not in ['y', 'n']:
            user_input = input("Invalid input. Please enter 'Y' or 'N':")
        if user_input.lower() == 'y':
            target_file = os.path.join(self.project_config.source_path, str(self.node_config.hsl_filename))
            
            module_content = ModuleParser(self.project_config.source_path).get_module_file_content(self.node_config)
            if len(target_file) == 0:
                target_file = os.path.join(self.project_config.source_path, str(self.node_config.hsl_filename))
            
            with open(target_file, 'w', encoding='iso-8859-15') as zf:
                zf.write(module_content)


    def _build_html(self):
        user_input = input(f"Do you want to build the Help file? (Y/N):")
        while user_input.lower() not in ['y', 'n']:
            user_input = input("Invalid input. Please enter 'Y' or 'N':")
        if user_input.lower() == 'y':
            html_parser = HTMLfileParser()
            html_parser.init(self.project_config, self.node_config)

            if html_parser.exists():
                user_input = input(f"The log file exists. Do you want to overwrite the existing HTML file? (Y/N):")
                while user_input.lower() not in ['y', 'n']:
                    user_input = input("Invalid input. Please enter 'Y' or 'N':")
                if user_input.lower() == 'n':
                    return 
            
            html_parser.build_html()
            html_parser.write_html()
            html_parser.copy_css()


    def _load_config(self):
        print(self.project_config.json_file)
        if self.project_config.json_file:
            json_file = os.path.join(self.project_config.source_path, self.project_config.json_file)
            with open(json_file, 'r', encoding='utf-8') as qf:
                content = qf.read()
                self.node_config = JSONfileParser().parse_json(content)
        
        elif self.project_config.yaml_file:
            yaml_file = os.path.join(self.project_config.source_path, self.project_config.yaml_file)
            with open(yaml_file, 'r', encoding='utf-8') as yf:
                content = yf.read()
                self.node_config = YAMLfileParser().parse_yaml(content)
        else:
            raise ValueError("No configuration file found. Please provide a JSON or YAML configuration file.")
        
        self.project_config.title = self.node_config.title
        self.project_config.category = self.node_config.category
        self.project_config.context = self.node_config.context
        self.project_config.has_stores = len(self.node_config.stores) > 0
        self.project_config.has_timers = len(self.node_config.timers) > 0
        self.project_config.has_translations = len(self.node_config.translations) > 0

    ## USER INPUT TO INITIALIZE PROJECT CONFIGURATION
    def request_input(self):
        self._node_category()
        self._node_context()
        self._stores_timers_tls() 

    def _stores_timers_tls(self):
        print( "Inputs and outputs are required to create a project.")
        
        user_input = input("Will this project have stores? (Y/N):")
        while user_input.lower() not in ['y', 'n']:
            user_input = input("Invalid input. Please enter 'Y' or 'N':")
        if user_input.lower() == 'y':
            self.project_config.has_stores = True

        user_input = input("Will this project have timers? (Y/N):")
        while user_input.lower() not in ['y', 'n']:
            user_input = input("Invalid input. Please enter 'Y' or 'N':")
        if user_input.lower() == 'y':
            self.project_config.has_timers = True

        user_input = input("Will this project have translations? (Y/N):")
        while user_input.lower() not in ['y', 'n']:
            user_input = input("Invalid input. Please enter 'Y' or 'N':")
        if user_input.lower() == 'y':
            self.project_config.has_translations = True
        
    def _node_context(self):
        user_input = input(f"Enter the project context [{self.node_config.context}]:") or self.node_config.context
        while not user_input:
            user_input = input("Invalid project context. Please enter a valid project context:")
        self.node_config.context = user_input

    def _node_category(self):
        user_input = input(f"Enter the project category [{self.node_config.category}]:") or "IOT Device Data"
        while not user_input:
            user_input = input("Invalid project category. Please enter a valid project category:")
        self.node_config.category = user_input
