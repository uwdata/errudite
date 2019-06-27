Domain Specific Language (DSL)
==============================

Errudite has a DSL language that: 

1. Use primitive functions that run on targets to extract fundamental instance metadata 
   (e.g., `length(premise)` returns the length of a question). 
2. Allows string command inputs, which can be automatically parsed into actual primitive functions. 
    The objective here is, we try to query the frequently used targets more easily for you. 
    On a high level, parser works as the following:
    - If it recognizes a target name that occurrs in `instance.entries`, it automatically retrive the target.
    - If it recognizes a registered primitive function, it runs the function.
    - It also supports more general operators like `>`, `<=`, `and`, `or`, etc.
    - It resolves previously created attributes ("attr:attr_name") and groups (("group:group_name")).

There is a basic wrapper class, `errudite.build_blocks.PrimFunc`, to wrap all the functions up.
Errudite also has a list of functions to support computing instance attributes 
and/or build instance groups. 

.. toctree::
    errudite.build_blocks.prim_func
    errudite.build_blocks.prim_funcs