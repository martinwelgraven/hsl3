import os
import re
from datetime import date
from typing import Optional

import yaml

from hsl3.hsl3_generator.configs.dcls_module import ConfigModule
from hsl3.hsl3_generator.configs.dcls_output import ConfigOutput
from hsl3.hsl3_generator.configs.dcls_input import ConfigInput
from hsl3.hsl3_generator.configs.dcls_project import ConfigProject
from hsl3.hsl3_generator.configs.dcls_store import ConfigStore
from hsl3.hsl3_generator.configs.dcls_timer import ConfigTimer
from hsl3.hsl3_generator.configs.dcls_script import ConfigScript
from hsl3.hsl3_generator.configs.dcls_translation import ConfigTranslation


def _replace_text_line_breaks(value: object) -> object:
    if isinstance(value, str):
        return value.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')
    if isinstance(value, list):
        return [_replace_text_line_breaks(item) for item in value]
    if isinstance(value, dict):
        return {key: _replace_text_line_breaks(item) for key, item in value.items()}
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
        root = _replace_text_line_breaks(yaml.safe_load(file_content))
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
            list_item = ConfigInput(**elem)
            inputs.append(list_item)

        for elem in module['outputs']:
            list_item = ConfigOutput(**elem)
            outputs.append(list_item)

        if 'stores' in module:
            for elem in module['stores']:
                list_item = ConfigStore(**elem)
                stores.append(list_item)

        if 'timers' in module:
            for elem in module['timers']:
                list_item = ConfigTimer(**elem)
                timers.append(list_item)

        for elem in module['scripts']:
            list_item = ConfigScript(**elem)
            scripts.append(list_item)

        if 'translations' in module:
            for elem in module['translations']:
                translation_inputs = []

                for ti in elem['translation_inputs']:
                    translation_inputs.append(ti['label'])
                translation_outputs = []

                for to in elem['translation_outputs']:
                    translation_outputs.append(to['label'])

                elem_dict = dict(elem)
                elem_dict['translation_inputs'] = translation_inputs
                elem_dict['translation_outputs'] = translation_outputs

                list_item = ConfigTranslation(**elem_dict)
                translations.append(list_item)

        module['inputs'] = inputs
        module['outputs'] = outputs
        module['stores'] = stores
        module['timers'] = timers
        module['scripts'] = scripts
        module['translations'] = translations

        return ConfigModule(**module)

    def write_first_yaml(self, config: ConfigProject):
        config_dict = {
            "module": {
                "id": config.id,
                "name": config.title,
                "version": "0.1.0",
                "version_date": date.today(),
                "description": "This is a description for the module.",
                "warning": "",
                "note": "",
                "category": config.category,
                "context": config.context,
                "hsl_filename": config.node_file,
                "inputs": [
                    {
                        "type": "string",
                        "identifier": "IN01",
                        "init_value": "",
                        "label": "Input 01",
                        "description": "This is a description for Input 01"
                    }
                ],
                "outputs": [
                    {
                        "type": "string",
                        "identifier": "OUT01",
                        "init_value": "",
                        "sbc": "s",
                        "label": "Output 01",
                        "description": "This is a description for Output 01"
                    }
                ],
                "stores": [
                    {
                        "identifier": "STORE01",
                        "type": "string",
                        "init_value": "",
                        "label": "Store 01",
                        "description": "This is a description for Store 01"
                    }
                ] if config.has_stores else [],
                "timers": [
                    {
                        "identifier": "TIMER01",
                        "description": "This is a description for Timer 01"
                    }
                ] if config.has_timers else [],
                "scripts": [
                    {
                        "filename": config.python_file
                    }
                ],
                "translations": [
                    {
                        "language": "en",
                        "category": "",
                        "name": "English",
                        "translation_inputs": [{"label": "Input 01"}],
                        "translation_outputs": [{"label": "Output 01"}]
                    }
                ] if config.has_translations else []
            }
        }

        with open(os.path.join(config.source_path, config.yaml_file), 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_dict, f, sort_keys=False, allow_unicode=True)

    def update_version(self, config: ConfigProject, version: str, version_date: str, note: Optional[str]):
        path = os.path.join(config.source_path, config.yaml_file)
        with open(path, 'r', encoding='utf-8', newline='') as f:
            content = f.read()

        root = yaml.compose(content, Loader=yaml.SafeLoader)
        expected = yaml.safe_load(content)
        if not isinstance(root, yaml.MappingNode) or not isinstance(expected, dict):
            raise ValueError("Invalid YAML format: expected a mapping at the root.")

        def find_member(mapping, name):
            matches = [(key, value) for key, value in mapping.value
                       if isinstance(key, yaml.ScalarNode) and key.value == name]
            if len(matches) != 1:
                raise ValueError(f"Invalid YAML format: expected one {name!r} key.")
            return matches[0]

        _, module = find_member(root, 'module')
        if not isinstance(module, yaml.MappingNode) or not isinstance(expected.get('module'), dict):
            raise ValueError("Invalid YAML format: 'module' must be a mapping.")

        parsed_date = date.fromisoformat(version_date)
        changes = {'version': version, 'version_date': version_date}
        if note is not None:
            changes['note'] = note.replace('\\n', '\n')
        replacements = []
        for key, value in changes.items():
            key_node, node = find_member(module, key)
            if not isinstance(node, yaml.ScalarNode):
                raise ValueError(f"Invalid YAML format: 'module.{key}' must be a scalar.")
            start, end = node.start_mark.index, node.end_mark.index
            if key == 'note':
                if module.flow_style:
                    raise ValueError("Cannot write a literal note in a flow-style YAML mapping.")
                literal = yaml.safe_dump(value, default_style='|', allow_unicode=True) if value else '|-\n'
                if literal.endswith('\n...\n'):
                    literal = literal[:-4]
                header, separator, body = literal.partition('\n')
                if not separator or not header.startswith('|'):
                    raise ValueError("Cannot represent the note as a YAML literal block.")

                header = '|-'

                newline = '\r\n' if '\r\n' in content else '\n'
                body_lines = body.splitlines(keepends=True)
                body = ''.join(
                    (' ' * key_node.start_mark.column + line if line.strip() else line)
                    for line in body_lines
                ).replace('\n', newline)
                if body.endswith(newline):
                    body = body[:-len(newline)]

                original = content[start:end]
                header_suffix = ''
                trailing_text = ''
                if node.style in ('|', '>'):
                    comment = re.search(r'[ \t]+#.*$', original.splitlines()[0])
                    if comment:
                        header_suffix = comment.group()
                    trailing = re.search(r'((?:\r\n|\r|\n)[ \t]*)+$', original)
                    if trailing:
                        trailing_text = trailing.group()
                else:
                    line_end = content.find('\n', end)
                    if line_end == -1:
                        line_end = len(content)
                    suffix = content[end:line_end].rstrip('\r')
                    if suffix and not re.fullmatch(r'[ \t]*(?:#.*)?', suffix):
                        raise ValueError("Cannot preserve text following the YAML note.")
                    header_suffix = suffix
                    end += len(suffix)
                    if line_end == len(content):
                        trailing_text = newline
                replacement = header + header_suffix + newline + body + trailing_text
            elif key == 'version_date':
                replacement = parsed_date.isoformat()
            else:
                if not value or any(char in value for char in '\r\n'):
                    raise ValueError(f"Invalid YAML format: 'module.{key}' must be a single-line string.")
                try:
                    plain_value = yaml.safe_load('value: ' + value)
                    tagged_value = yaml.safe_load('value: !!str ' + value)
                except yaml.YAMLError:
                    plain_value = tagged_value = None
                if plain_value == {'value': value}:
                    replacement = value
                elif tagged_value == {'value': value}:
                    replacement = '!!str ' + value
                else:
                    replacement = "'" + value.replace("'", "''") + "'"
            replacements.append((start, end, replacement))
        for start, end, value in sorted(replacements, reverse=True):
            content = content[:start] + value + content[end:]

        expected['module'].update(changes)
        expected['module']['version_date'] = parsed_date
        if yaml.safe_load(content) != expected:
            raise ValueError("Cannot update YAML without changing other configuration values.")

        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)