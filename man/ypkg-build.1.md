ypkg-build(1) -- Build Solus ypkg files
=======================================


## SYNOPSIS

`ypkg-build <flags> [package.yml]`


## DESCRIPTION

`ypkg-build` is the main component of the `ypkg(1)` package. Given a `package.yml(5)`
file, it will attempt to build the package according to the rules, patterns and
steps set in the file.

For details on the package format itself, please refer to the `package.yml(5)`
manpage, or the Solus wiki.

Note that you should not use `ypkg-build(1)` directly unless completely unavoidable.
Instead, you should be using `solbuild(1)` for isolated build environments.

## OPTIONS

The following options are applicable to `ypkg-build(1)`.

 * `-h`, `--help`

   Print the command line options for `ypkg(1)` and exit.

 * `-v`, `--version`

   Print the `ypkg(1)` version and exit.

 * `-n`, `--no-colors`

   Disable text colourisation in the output from `ypkg` and all child
   processes.

 * `-t`, `--timestamp`

   This argument should be a UNIX timestamp, and will be used to set the file
   timestamps inside the final `.eopkg` archive, as well as the container files
   within that archive.

   Using this option helps achieve a level of reproducability in builds, and
   this option is passed by `solbuild(1)` automatically for ypkg builds. It
   will examine the git history and use the UTC UNIX timestamp for the last
   tag, ensuring the package can be built by any machine using `solbuild(1)`
   and result in an identical package, byte for byte.

 * `-D`, `--output-dir`

   Set the output directory for `ypkg-build(1)`


## EXIT STATUS

On success, 0 is returned. A non-zero return code signals a failure.


## COPYRIGHT

 * Copyright © 2016 Ikey Doherty, License: CC-BY-SA-3.0


## SEE ALSO

`solbuild(1)`, `ypkg-install-deps(1)`, `ypkg(1)`, `package.yml(5)`

 * https://github.com/solus-project/ypkg
 * https://wiki.solus-project.com/Packaging


## NOTES

Creative Commons Attribution-ShareAlike 3.0 Unported

 * http://creativecommons.org/licenses/by-sa/3.0/
