Epidoc Conversion Tools
------

A small module for making old TEI XML (somewhat) Epidoc-compliant. This is pre-pre-alpha software and essentially designed only for internal use. Use at your own risk.

## Overview

See [epidoc_conversion/converter.py](epidoc_conversion/converter.py).

## Installation

It's strongly recommended to set up a [virtual environment](https://docs.python.org/3/library/venv.html) in the directory where you'll be working:

```sh
$ python -m venv .venv
```

Then, activate your venv and install this module from GitHub:

```sh
$ source .venv/bin/activate
$ pip install git+https://github.com/pletcher/epidoc_conversion.git
```

> [!NOTE]
> If you are using [uv](https://docs.astral.sh/uv/), you'll need to adjust the above commands accordingly.

## Usage

After installation, you can run the script via the `convert` command:

```sh
$ convert path/to/xml/to/update.xml
```

> [!IMPORTANT]
> The converter will update the file _in place_, meaning it will overwrite any unsaved changes if you are currently working on the file.
> If, however, you have the (saved) file open in your text editor, you can `cmd/ctrl-Z` after running the script to undo its changes.

# License

The MIT License

Copyright (c) 2025 The Perseus Project

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
