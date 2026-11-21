import os
import re
from datetime import date
from typing import Optional
from enum import Enum

import yaml

from hsl3.hsl3_generator.configs.dcls_module import ConfigModule
from hsl3.hsl3_generator.configs.dcls_output import ConfigOutput
from hsl3.hsl3_generator.configs.dcls_input import ConfigInput
from hsl3.hsl3_generator.configs.dcls_project import ConfigProject
from hsl3.hsl3_generator.configs.dcls_store import ConfigStore
from hsl3.hsl3_generator.configs.dcls_timer import ConfigTimer
from hsl3.hsl3_generator.configs.dcls_script import ConfigScript
from hsl3.hsl3_generator.configs.dcls_translation import ConfigTranslation, ConfigTranslationInput, ConfigTranslationOutput


def _replace_text_line_breaks(value: str) -> str:
   return value.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')
   

def _to_yaml_value(value, memo=None):
    """Convert complex objects to YAML-serializable primitives recursively.
    
    Handles: dicts, lists, tuples, Enum values, dataclass instances, and primitives.
    Uses memo dict to track already-converted objects and prevent infinite loops.
    """
    if memo is None:
        memo = {}

    # Handle Enum values first - convert to their name string
    if isinstance(value, Enum):
        return value.name
    
    # Handle primitives that are YAML-safe
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    
    # Handle bytes - decode to string
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    
    # Handle date objects - convert to ISO format string
    if isinstance(value, date):
        return value.isoformat()
    
    # Handle dictionaries
    if isinstance(value, dict):
        if id(value) in memo:
            return memo[id(value)]
        result = {}
        memo[id(value)] = result
        result.update((key, _to_yaml_value(item, memo)) for key, item in value.items())
        return result
    
    # Handle lists and tuples
    if isinstance(value, (list, tuple)):
        if id(value) in memo:
            return memo[id(value)]
        result = []
        memo[id(value)] = result
        result.extend(_to_yaml_value(item, memo) for item in value)
        return result
    
    # Handle objects with __dict__ (dataclasses, custom objects)
    if hasattr(value, '__dict__'):
        if id(value) in memo:
            return memo[id(value)]
        result = {}
        memo[id(value)] = result
        result.update((key, _to_yaml_value(item, memo)) for key, item in vars(value).items())
        return result
    
    # Fallback for any other type
    return value


class YAMLfileParser:
    """Class for parsing the YAML configuration file for a logic module."""

    def read_note(self, config: ConfigProject) -> str:
        path = os.path.join(config.source_path, config.yaml_file)
        with open(path, 'r', encoding='utf-8') as f:
            root = yaml.safe_load(f)
        if not isinstance(root, dict) or not isinstance(root.get('module'), dict):
            raise ValueError("Invalid YAML format: 'module' must be a mapping.")
        note = root['module'].get('note', '')
        if not isinstance(note, str):
            raise ValueError("Invalid YAML format: 'module.note' must be a string.")
        return note

    def parse_yaml(self, file_content):
        root = yaml.safe_load(file_content)
        if not isinstance(root, dict):
            raise TypeError("Invalid YAML format: expected a mapping at the root.")

        module = root.get('module')
        if not isinstance(module, dict):
            raise TypeError("Invalid YAML format: 'module' must be a mapping.")

        if isinstance(module.get('version_date'), date):
            module['version_date'] = module['version_date'].isoformat()

        required_lists = ('inputs', 'outputs', 'scripts')
        if any(not isinstance(module.get(key), list) for key in required_lists):
            raise TypeError("Invalid YAML format: 'module' must contain input, output, and script lists.")

        inputs = []
        outputs = []
        stores = []
        timers = []
        scripts = []

        translations = []

        for elem in module['inputs']:
            list_item = ConfigInput(
                label=elem['label'],
                type=elem['type'],
                init_value=elem['init_value'],
                identifier=elem.get('identifier', ''),
                description=elem.get('description', '')
            )
            inputs.append(list_item)

        for elem in module['outputs']:
            list_item = ConfigOutput(
                label=elem['label'],
                type=elem['type'],
                init_value=elem['init_value'],
                identifier=elem.get('identifier', ''),
                description=elem.get('description', '')
            )
            outputs.append(list_item)

        if 'stores' in module:
            for elem in module['stores']:
                list_item = ConfigStore(
                    type=elem['type'],
                    init_value=elem['init_value'],
                    identifier=elem.get('identifier', ''),
                    description=elem.get('description', '')
                )
                stores.append(list_item)

        if 'timers' in module:
            for elem in module['timers']:
                list_item = ConfigTimer(
                    identifier=elem.get('identifier', ''),
                    description=elem.get('description', '') 
                )
                timers.append(list_item)

        for elem in module['scripts']:
            list_item = ConfigScript(
                filename=elem.get('filename', ''),
                folder=elem.get('folder', '')
            )
            scripts.append(list_item)

        if 'translations' in module:
            for elem in module['translations']:
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

        module['inputs'] = inputs
        module['outputs'] = outputs
        module['stores'] = stores
        module['timers'] = timers
        module['scripts'] = scripts
        module['translations'] = translations

        return ConfigModule(**module)

    
    def write_yaml(self, project_config: ConfigProject, node_config: ConfigModule):
        description = node_config.description
        node_config.description = _replace_text_line_breaks(description)

        warning = node_config.warning
        node_config.warning = _replace_text_line_breaks(warning)

        note = node_config.note
        node_config.note = _replace_text_line_breaks(note)

        node_dict = {'module': _to_yaml_value(node_config)}
        with open(os.path.join(project_config.source_path, project_config.yaml_file), 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                node_dict,
                f,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
            )

    def open_yaml(self, project_config: ConfigProject) -> dict:
        path = os.path.join(project_config.source_path, project_config.yaml_file)
        with open(path, 'r', encoding='utf-8', newline='') as f:
            content = f.read()

        expected: dict = yaml.safe_load(content)
        if not isinstance(expected, dict):
            raise ValueError("Invalid YAML format: expected a mapping at the root.")
        elif 'module' not in expected.keys():
            raise ValueError("Invalid YAML format: expected at least one key.")
        else:
            return expected


    def update_version(self, project_config: ConfigProject, version: str, version_date: str, note: Optional[str]):
        
        node_config = self.open_yaml(project_config)
        node_config['module']['version'] = version
        node_config['module']['version_date'] = date.fromisoformat(version_date)
        if note is not None:
            node_config['module']['note'] = note

        self.write_yaml(project_config, ConfigModule(**node_config['module']))