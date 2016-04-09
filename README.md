ypkg2
-----

ypkg is the build tool of choice for the Solus Operating System. Simply put, it
is a tool to convert a build process into a packaging operation.

ypkg evolved from a simple set of ideas within the Solus Project, that packaging
should be simple. Given rules should be obeyed globally, and where appropriate
the packager should be able to tweak the results to how they desire.

This grew.. organically. As it stands, much of the code is actually very nasty,
and could be more efficient. Secondly, we formulate a fake pspec/actions combo
to relay back to eopkg itself, relying on what we **understand** about the package,
to eopkg's legacy concept of file accounting, which differs wildly from our own
rules.

**How Rules Work:**

Everything in ypkg can be traced to a *pattern*. We use these to define what part
of a package, or sub-package, a file should be placed in. To enforce consistency,
we have our own in-built patterns, i.e.:

    /usr/lib64/lib*.so   = devel subpackage
    /usr/lib64/lib*.so.* = "main" package

There are many in-built patterns which designate how the subpackages should be
emitted, allowing for self resolving dependency graphs:

    dev: depends on "main":
        /usr/lib64/pkgconfig/*.pc
        /usr/lib64/lib*.so
    dev: also depends on whatever the pkgconfig files depend on

    main: shared library dependencies:
        /usr/lib64/lib*.so.*

However, sometime's it is desirable to split up a package. Consider this example:

    main:
        /usr/lib64/libpoppler-glib.so.*
        /usr/lib64/libpoppler-qt5*.so.*
    devel:
        /usr/lib64/lib*.so

The automatic behaviour would by default make the main package gain a dependency
on the `qt5` package, through direct binary dependencies. This can be very undesirable
and would cause unnecessary bloat in lighter systems.

The solution, therefore, is to do the following:

    main:
        /usr/lib64/lib*.so.*
    devel:
        /usr/lib64/lib*.so
        /usr/lib64/pkgconfig/*.pc

    qt5:
        /usr/lib64/libpoppler-qt5*.so.*
    qt5-devel:
        /usr/lib64/libpoppler-qt5*.so
        /usr/lib64/pkgconfig/poppler-qt5.pc

However, we see that the pattern for both main and devel will capture files that
have been destined for qt5 and qt5-devel subpackages. There is no simple way to
express this when passing by proxy to a package builder, therefore **ypkg2 will
have to build the packages itself**.

License
-------

GPL-3.0

Copyright (C) 2016 Ikey Doherty

Some portions: Copyright (C) 2016 Intel Corporation
Some elements have been gratefully borrowed from autospec:

https://github.com/clearlinux/autospec


The TODO:
---------

 * [x] Write a new CLI frontend that's option based this time
 * [x] Add class-based `YpkgSpec` to represent the `package.yml` input file
 * [x] Add dedicated parser
 * [x] Split dependency install out from main ypkg routine
 * [x] Add **extensible** macros
 * [x] Add the string-based path globbing algo
 * [x] Add necessary logic to dynamically emit the `YpkgPackage` objects
 * [x] Emit our first native `.eopkg`
 * [x] Fold in our dynamic dependency scanning from `eopkg` into `ypkg`
 * [x] Add stripping
 * [x] Add enhanced `debuginfo` packages
 * [x] Support solus packager file
 * [x] Support history.xml file (evobuild will generate this.)
 * [ ] Release "ypkg2"
 * [ ] Add support for reproducible builds
