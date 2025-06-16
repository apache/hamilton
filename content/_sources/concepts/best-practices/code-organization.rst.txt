=================
Code Organization
=================

Apache Hamilton will force you to organize your code! Here's some tips.

Apache Hamilton forces you to put your code into modules that are distinct from where you run your code.

You'll soon find that a single python module does not make sense, and so you'll organically start to (very likely) put
like functions with like functions, i.e. thus creating domain specific modules --> `use this to your development
advantage!`

At Stitch Fix we:

#. Use modules to model team thinking, e.g. date\_features.py.
#. Use modules to helps isolate what you’re working on.
#. Use modules to replace parts of your Apache Hamilton dataflow very easily for different contexts.

Team thinking
-------------

You'll need to curate your modules. We suggest orienting this around how teams think about the business.

E.g. marketing spend features should be in the same module, or in separate modules but in the same directory/package.

This will then make it easy for people to browse the code base and discover what is available.

Helps isolate what you're working on
------------------------------------

Grouping functions into modules then helps set the tone for what you're working on. It helps set the "namespace", if
you will, for that function. Thus you can have the same function name used in multiple modules, as long as only one of
those modules is imported to build the DAG.

Thus modules help you create boundaries in your code base to isolate functions that you'll want to change inputs to.

Enables you to replace parts of your DAG easily for different contexts
----------------------------------------------------------------------

The names you provide as inputs to functions form a defined "interface", to borrow a computer science term, so if you
want to swap/change/augment an input, having a function that would map to it defined in another module(s) provides a
lot of flexibility. Rather than having a single module with all functions defined in it, separating the functions into
different modules could be a productivity win.

Why? That's because when you come to tell Apache Hamilton what functions constitute your dataflow (i.e. DAG), you'll be able
to simply replace/add/change the module being passed. So if you want to compute inputs for certain functions
differently, this composability of including/excluding modules, when building the DAG provides a lot of flexibility
that you can exploit to make your development cycle faster.
