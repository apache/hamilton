=============================
Function modifiers (Advanced)
=============================

.. warning::

    This page is a work in progress. Refer to the API reference for more documentation and please ask a public question on `Slack <https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g>`_ if you need help!

The page :doc:`function-modifiers` details how to use decorators to write expressive dataflows. The e presented function modifiers are highly expressive and should be sufficient in the large majority of cases.

Nonetheless, there exists higher level abstractions for power users that *may* be useful for integrations with your existing platform. If you want to use complex machinery instead of writing 1 additional function, comeback when it's your 10th manually addition 🛠

This page assumes an advanced understanding of Apache Hamilton and will cover:

- @pipe
- @subdag
- @parameterize_subdag
- @resolve
