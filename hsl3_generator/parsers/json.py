import os
import json
from dataclasses import asdict
from datetime import date
from typing import Optional
from enum import Enum

from hsl3.hsl3_generator.configs.dcls_module import ConfigModule
from hsl3.hsl3_generator.configs.dcls_output import ConfigOutput
from hsl3.hsl3_generator.configs.dcls_input import ConfigInput
from hsl3.hsl3_generator.configs.dcls_project import ConfigProject
from hsl3.hsl3_generator.configs.dcls_store import ConfigStore
from hsl3.hsl3_generator.configs.dcls_timer import ConfigTimer
from hsl3.hsl3_generator.configs.dcls_script import ConfigScript
from hsl3.hsl3_generator.configs.dcls_translation import ConfigTranslation, ConfigTranslationOutput, ConfigTranslationInput


def _to_json_value(value):
    """Convert complex objects to JSON-serializable primitives.
    
    Handles: Enums (convert to name), dates (to ISO format), and nested structures.
    """
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    if isinstance(value, dict):
        return {key: _to_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_value(item) for item in value]
    return value


class JSONfileParser:
    """ Class for parsing the JSON configuration file for a logic module. """

    
    def parse_json(self, file_content):
        root = json.loads(file_content)
        inputs = []
        outputs = []
        stores = []
        timers = []
        scripts = []
        
        translations = []
        
        for elem in root['module']['inputs']:
            list_item = ConfigInput(
                label=elem['label'],
                type=elem['type'],
                init_value=elem['init_value'],
                identifier=elem.get('identifier', ''),
                description=elem.get('description', '')
            )
            inputs.append(list_item)
        
        for elem in root['module']['outputs']:
            list_item = ConfigOutput(
                label=elem['label'],
                type=elem['type'],
                init_value=elem['init_value'],
                identifier=elem.get('identifier', ''),
                description=elem.get('description', '')
            )
            outputs.append(list_item)
        
        if 'stores' in root['module']:
            for elem in root['module']['stores']:
                list_item = ConfigStore(
                    type=elem['type'],
                    init_value=elem['init_value'],
                    identifier=elem.get('identifier', ''),
                    description=elem.get('description', '')
                )
                stores.append(list_item)
        
        if 'timers' in root['module']:
            for elem in root['module']['timers']:
                list_item = ConfigTimer(
                    identifier=elem.get('identifier', ''),
                    description=elem.get('description', '') 
                )
                timers.append(list_item)
        
        for elem in root['module']['scripts']:
            list_item = ConfigScript(
                filename=elem.get('filename', ''),
                folder=elem.get('folder', '')
            )
            scripts.append(list_item)
        
        if 'translations' in root['module']:
            for elem in root['module']['translations']:
                translation_inputs = []
                for ti in elem['translation_inputs']:
                    translation_input = ConfigTranslationInput(
                        label=ti['label']
                    )
                    translation_inputs.append(translation_input)


                translation_outputs = []
                for to in elem['translation_outputs']:
                    translation_output = ConfigTranslationOutput(
                        label=to['label']
                    )
                    translation_outputs.append(translation_output)

                translation = ConfigTranslation(
                    category=elem.get('category', ''),
                    language=elem.get('language', ''),
                    name=elem.get('name', ''),
                    translation_inputs=translation_inputs,
                    translation_outputs=translation_outputs
                )

                translations.append(translation)
        
        root['module']['inputs'] = inputs
        root['module']['outputs'] = outputs
        root['module']['stores'] = stores
        root['module']['timers'] = timers
        root['module']['scripts'] = scripts
        root['module']['translations'] = translations

        return ConfigModule(**root['module'])


    def unparse_json(self, node_config: ConfigModule) -> dict:
        def without_private_elements(value):
            if isinstance(value, dict):
                return {
                    key: without_private_elements(item)
                    for key, item in value.items()
                    if not key.startswith('_')
                }
            if isinstance(value, list):
                return [without_private_elements(item) for item in value]
            return value

        module = without_private_elements(asdict(node_config))
        # Convert Enums, dates, and bytes to JSON-serializable values
        module = _to_json_value(module)
        return {'module': module}

    def write_json(self, project_config: ConfigProject, node_config: ConfigModule):
        with open(os.path.join(project_config.source_path, project_config.json_file), 'w', encoding='utf-8') as f:
            json.dump(self.unparse_json(node_config), f, default=str, indent=4, ensure_ascii=False)

    def open_json(self, project_config: ConfigProject) -> dict:
        path = os.path.join(project_config.source_path, project_config.json_file)
        with open(path, 'r', encoding='utf-8', newline='') as f:
            content = f.read()

        expected: dict = json.loads(content)
        if not isinstance(expected, dict):
            raise ValueError("Invalid JSON format: expected a mapping at the root.")
        elif 'module' not in expected.keys():
            raise ValueError("Invalid JSON format: expected at least one key.")
        else:
            return expected

    def update_version(self, project_config: ConfigProject, version: str, version_date: str, note: Optional[str]):
            
        node_config = self.open_json(project_config)
        node_config['module']['version'] = version
        node_config['module']['version_date'] = date.fromisoformat(version_date)
        if note is not None:
            node_config['module']['note'] = note

        self.write_json(project_config, ConfigModule(**node_config['module']))
