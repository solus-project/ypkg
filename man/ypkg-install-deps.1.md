ypkg-install-deps(1) -- Install build dependencies
==================================================


## SYNOPSIS

`ypkg-install-deps <flags> [package.yml]`


## DESCRIPTION

`ypkg-install-deps` will install all of the build dependencies listed in the
given `package.yml(5)` file. Note that resolution of `pkgconfig` and `pkgconfig32`
dependencies is handled automatically.

## OPTIONS

The following options are applicable to `ypkg-install-deps(1)`.

 * `-h`, `--help`

   Print the command line options for `ypkg(1)` and exit.

 * `-v`, `--version`

   Print the `ypkg(1)` version and exit.

 * `-n`, `--no-colors`

   Disable text colourisation in the output from `ypkg` and all child
   processes.

 * `-D`, `--output-dir`

   This option is ignored by `ypkg-install-deps(1)`. It is provided simply
   for compatibility in scripting to allow `ypkg(1)` to pass arguments forward
   for the duration of the session.

 * `-f`, `--force`

   Force the installation of package dependencies, which will bypass any
   prompting by ypkg. The default behaviour is to prompt before installing
   packages.


## EXIT STATUS

On success, 0 is returned. A non-zero return code signals a failure.


## COPYRIGHT

 * Copyright © 2016 Ikey Doherty, License: CC-BY-SA-3.0


## SEE ALSO

`solbuild(1)`, `ypkg(1)` `ypkg-build(1)`, `package.yml(5)`

 * https://github.com/solus-project/ypkg
 * https://wiki.solus-project.com/Packaging


## NOTES

Creative Commons Attribution-ShareAlike 3.0 Unported

 * http://creativecommons.org/licenses/by-sa/3.0/
