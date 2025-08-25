import os
import configparser
from pathlib import Path
from typing import Dict, Any

class Config:
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = Path(__file__).parent.parent / "config.ini"
        self.load_config()
    
    def load_config(self) -> None:
        if self.config_file.exists():
            self.config.read(self.config_file)
    
    def save_config(self, config_data: Dict[str, str]) -> None:
        self.config['DEFAULT'] = config_data
        
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
    
    @property
    def supabase_url(self) -> str:
        return self.config.get('DEFAULT', 'supabase_url', fallback='')
    
    @property
    def supabase_key(self) -> str:
        return self.config.get('DEFAULT', 'supabase_key', fallback='')
    
    @property
    def openai_key(self) -> str:
        return self.config.get('DEFAULT', 'openai_key', fallback='')
    
    @property
    def api_host(self) -> str:
        return self.config.get('DEFAULT', 'api_host', fallback='0.0.0.0')
    
    @property
    def api_port(self) -> int:
        return self.config.getint('DEFAULT', 'api_port', fallback=8000)
    
    def is_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_key and self.openai_key)

config = Config() 