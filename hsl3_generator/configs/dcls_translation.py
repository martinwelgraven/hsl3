from dataclasses import dataclass, field
from typing import List

@dataclass
class ConfigTranslationInput:
    label: str
    index: int = field(init=False)
    _next_id: int = field(default=1, init=False, repr=False)
    
    def __post_init__(self):
        self.index = ConfigTranslationInput._next_id
        ConfigTranslationInput._next_id += 1

@dataclass
class ConfigTranslationOutput:
    label: str
    index: int = field(init=False)
    _next_id: int = field(default=1, init=False, repr=False)
    
    def __post_init__(self):
        self.index = ConfigTranslationOutput._next_id
        ConfigTranslationOutput._next_id += 1

@dataclass
class ConfigTranslation:
    category: str
    language: str
    name: str
    index: int = field(init=False)
    translation_inputs: List[ConfigTranslationInput]
    translation_outputs: List[ConfigTranslationOutput]
    _next_id: int = field(default=1, init=False, repr=False)
    
    def __post_init__(self):
        self.index = ConfigTranslation._next_id
        ConfigTranslation._next_id += 1

