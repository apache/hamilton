==============
Packaging
==============

Subgraph packaging for Hamilton dataflows. A :class:`hamilton.packaging.NodePackage`
carves a group of nodes out of a driver's built internal graph (``Driver.graph``) and
treats it as a first-class, reusable unit that records the nodes it provides, the
external dependencies it requires, the configuration keys it needs, and the dependency
edges among them. Packages serialize to JSON manifests for export and import, validate
for compatibility against a host dataflow's graph, detect conflicts against other
packages, and compose deterministically into larger packages. Packages supplied with
``Builder.with_packages(...)`` are enforced when the driver is built.

NodePackage
-----------

.. autoclass:: hamilton.packaging.NodePackage
   :members:

PackageManifest
---------------

.. autoclass:: hamilton.packaging.PackageManifest
   :members:

Validation results
------------------

.. autoclass:: hamilton.packaging.ValidationReport
   :members:

.. autoclass:: hamilton.packaging.ValidationProblem
   :members:

Conflicts
---------

.. autoclass:: hamilton.packaging.PackageConflict
   :members:

Diffs
-----

.. autoclass:: hamilton.packaging.ManifestDiff
   :members:

Errors
------

.. autoclass:: hamilton.packaging.PackagingError

.. autoclass:: hamilton.packaging.PackageValidationError

.. autoclass:: hamilton.packaging.PackageConflictError

Module-level helpers
--------------------

.. autofunction:: hamilton.packaging.validate_package

.. autofunction:: hamilton.packaging.find_conflicts

.. autofunction:: hamilton.packaging.compose_packages

.. autofunction:: hamilton.packaging.diff_manifests

.. autofunction:: hamilton.packaging.export_package

.. autofunction:: hamilton.packaging.import_manifest

Driver integration
------------------

Packages integrate with the driver lifecycle:

* ``Builder.with_packages(*node_packages)`` declares the packages a dataflow must be
  compatible with.
* Building a driver validates its graph against every declared package, raising
  :class:`hamilton.packaging.PackageValidationError` when one is incompatible.
* ``Driver.list_packages()`` returns the declared packages and
  ``Driver.validate_packages()`` returns one report per package.
