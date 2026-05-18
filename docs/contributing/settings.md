## Project Configuration Usage Guide

All project configuration is managed centrally by `chatchat.settings.Settings`, replacing the previous approach of using `chatchat/configs/*.py`.

The vast majority of configuration items retain their original names and groupings; a few have been consolidated.

### Benefits After the Improvement:
- Configuration is separated from py code, reducing hassle when upgrading code and making configuration changes easier
- Switching to a different yaml file loads a different configuration, making multi-environment management and testing more convenient
- Configuration items are defined via `pydantic` models, strengthening data validation, simplifying environment variable reading, and supporting different file backends such as `yaml/json/toml`
- yaml file templates can be auto-generated, with configuration descriptions included
- All configuration items are cached to reduce file reads; when the .yaml/.env file is modified, the cache is automatically refreshed
  
### Usage:

```python3
from chatchat.settings import Settings

print(Settings.basic_settings) # basic configuration, including data directory, server settings, etc.
print(Settings.kb_settings) # knowledge base related configuration
print(Settings.model_settings) # model related configuration
print(Settings.tool_settings) # tool related configuration
print(Settings.prompt_settings) # prompt templates

```

** Note **: If you use the `Settings.xx_settings.XX` form, the configuration values will automatically track and refresh when the configuration file is modified. If you use the form `s = Settings.xx_settings; s.XX`, the configuration will not be automatically refreshed.

### Adding or Changing a Configuration Item:

Step 1: Add a field directly to the corresponding XXSettings class in `chatchat/settings.py`. Recommendations:
- Set a default value for every field
- Add necessary descriptions for the field

Step 2: Run `CHATCHAT_ROOT=/path/to/data chatchat init --gen-config` to update the configuration template.
