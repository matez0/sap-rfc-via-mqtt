[![Python versions](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![license](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

# SAP RFC via MQTT

## Testing

Create the virtual environment:
```
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -r requirements-testing.txt
```

For testing MQTT communication, clone [Paho Testing Utilities](https://github.com/eclipse/paho.mqtt.testing):
```
git clone https://github.com/eclipse/paho.mqtt.testing.git
```
Run the tests:
```
pytest tests -v
```
