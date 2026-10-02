This module needs the `pypdf` Python library in the environment Odoo runs in:

``` bash
pip install pypdf
```

If `pymupdf` is also installed, it is tried first, since it usually yields a
better text extraction; `pypdf` is used as the fallback.
