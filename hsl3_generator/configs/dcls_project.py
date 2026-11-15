import os
import re
from dataclasses import dataclass, field
import json
from typing import Optional

from hsl3.hsl3_generator.configs.dcls_module import ConfigModule


@dataclass
class ConfigProject:

    root: str
    state: str = 'new'
    
    id: str = ''
    name: str = ''
    title: str = ''
    category: str = ''
    context: str = ''

    has_timers: bool = False
    has_stores: bool = False
    has_translations: bool = False
    
    source_path: str = ''
    json_file: str = ''
    html_file: str = ''
    python_file: str = ''
    node_file: str = ''


    def __post_init__(self):
        if self.root is None:
           print('Root directory could not be retrieved. Process exits with error code 1.')
           exit(1)

        paths = self.root.split(os.sep)
        if not paths[len(paths)-1].startswith('hsl3-'):
            print(f"Root directory '{self.root}' is not valid. It should start with 'hsl3-' followed by the project name. Process exits with error code 1.")
            exit(1)

        self.name = paths[len(paths)-1][len('hsl3-'):]
        
        if not os.path.exists(self.root):
            print(f"Root directory '{self.root}' could not be validated. Process exits with error code 1.")
            exit(1)
        else:
            self.source_path = os.path.join(self.root, 'src', 'hsl3_' + self.name.replace('-','_'))
            self.json_file = f"config_{self.name.lower()}.json"
            tmp_config = json.load(open(os.path.join(self.source_path, self.json_file))) if os.path.exists(os.path.join(self.source_path, self.json_file)) else None
            if tmp_config:
                mod = tmp_config.get('module', '')
                self.id = mod.get('id', '')
                
            self.html_file = f"log{str(self.id)}.html"
            self.python_file = f"hsl3_{self.id}_{self.name.replace('-','_').lower()}.py"
            self.node_file = f"{self.id}_{self.name.replace('-','_').lower()}.hsl"
            
            if not os.path.exists(self.source_path):
                os.mkdir(self.source_path)
                self.state = 'initialized'
            elif not os.path.exists(os.path.join(self.source_path, self.json_file)):
                self.state = 'initialized'
            else:
                self.state = 'load'
        
        