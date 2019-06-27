Rewrite rules defined by DSL
============================

A rewrite rule is specified using the syntax ``rewrite(target,from -> to)``, 
where target indicates the part of the instance that should be rewritten by replacing from with to. 
Depending on whether or not you want to use linguistic features, you could use either ``RewriteStr``,
or ``RewritePattern``.

.. toctree::
    errudite.rewrites.replace_str
    errudite.rewrites.replace_pattern