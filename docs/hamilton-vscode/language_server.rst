---------------
Language Server
---------------

.. warning::

    The Apache Hamilton Language Server is an experimental feature under active development. Edge cases, evolving features, and partial documentation are to be expected. Please  open a GitHub issue or reach out on Slack for troubleshooting!


The Apache Hamilton Language Server is an implementation of the `Language Server Protocol (LSP) <https://microsoft.github.io/language-server-protocol/>`_. It is designed to power the :doc:`Apache Hamilton VSCode extension <./vscode_extension>` which can be installed directly from the `VSCode marketplace <https://marketplace.visualstudio.com/items?itemName=DAGWorks.hamilton-vsc>`_.

Language servers power IDE features like completion suggestion, go to definition, collect document symbols, etc. The LSP standard was established to make servers portable across IDE frontends (e.g., VSCode, PyCharm, Emacs). `Learn more <https://code.visualstudio.com/api/language-extensions/language-server-extension-guide>`_.

Installation
------------

If you're using the Apache Hamilton VSCode extension, you will prompted to install the language server if it's not found. Simply click the button and it will install it in your current Python interpreter.

You can also manually install the language server in your Python environment via

.. code:: shell

    pip install "sf-hamilton[lsp]"


Developers
----------

If you want to dig in the internals of the language server and integrate it with another IDE, you can find the source code in the ``dev tools/`` section of the `Apache Hamilton GitHub repository <https://github.com/apache/hamilton/tree/main/dev_tools/lsp>`_. It is also directly available on PyPi at `sf-hamilton-lsp <https://pypi.org/project/sf-hamilton-lsp/>`_.

Note that the package name is ``hamilton_lsp`` when used directly via Python code.
