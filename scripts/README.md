# Data extraction helpers

`scripts/extract_first_pc.py` decodes the binary dataset produced for the
WebGL viewer and writes the values for the "First PC" dataset into a JSON
file that can be consumed easily from Python.

```bash
python scripts/extract_first_pc.py
```

Running the script creates `first_pc.json` in the repository root with the
following structure:

```json
{
  "dtype": "float32",
  "shape": [134877],
  "data": [ ... values ... ]
}
```

You can load the JSON file in Python with:

```python
import json
from array import array

with open("first_pc.json") as fh:
    payload = json.load(fh)
first_pc = array('f', payload["data"])
```
