Epidoc Conversion Tools
------

A small module for making old TEI XML Epidoc-compliant.

# Overview

See [epidoc_conversion/converter.py](epidoc_conversion/converter.py).

# Using the converter as a script

After installing [poetry](https://python-poetry.org/docs/), run

```sh
$ poetry install
```

from the root directory of this repository. The activate the virtual environment for your current shell:

```sh
$ poetry shell
```

The converter script accepts just one argument, the `filename` (including relevant path information) of the TEI XML document that you wish to update.


```sh
$ python epidoc_conversion/converter.py path/to/tei_xml.xml
```

**NOTA BENE**: The converter will update the file _in place_, meaning it will overwrite any unsaved changes if you are currently working on the file.

If, however, you have the (saved) file open in (e.g.) VS Code, you can `cmd/ctrl-Z` after running the script to undo its changes.

# License

The MIT License

Copyright 2023 scaife.perseus.org

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.