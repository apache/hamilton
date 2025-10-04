import tomli
from pathlib import Path

toml_path = Path('tests/cli/resources/test_context.toml')
with open(toml_path, 'rb') as f:
    data = tomli.load(f)
print('TOML data:', data)