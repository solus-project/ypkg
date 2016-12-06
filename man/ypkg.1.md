ypkg(1) -- Build Solus ypkg files
=================================


## SYNOPSIS

`ypkg <flags> [package.yml]`


## DESCRIPTION

`ypkg` is the main entry point into `package.yml(5)` program. It is a stub that
will first call out to `ypkg-install-deps(1)` before passing off to `ypkg-build(1)`.
See those manpages for more details.

Note that you should not use `ypkg(1)` directly unless completely unavoidable.
Instead, you should be using `solbuild(1)` for isolated build environments.

## OPTIONS

These options apply to all subcommands within `solbuild(1)`.

 * `-h`, `--help`

   Print the command line options for `ypkg(1)` and exit.

 * `-v`, `--version`

   Print the `ypkg(1)` version and exit.

 * `-n`, `--no-colors`

   Disable text colourisation in the output from `ypkg` and all child
   processes.

 * `-D`, `--output-dir`

   Set the output directory for `ypkg-build(1)`

 * `-f`, `--force`

   Force the installation of package dependencies, which will bypass any
   prompting by ypkg. The default behaviour is to prompt before installing
   packages.


## EXIT STATUS

On success, 0 is returned. A non-zero return code signals a failure.


## COPYRIGHT

 * Copyright © 2016 Ikey Doherty, License: CC-BY-SA-3.0


## SEE ALSO

`solbuild(1)`, `ypkg-install-deps(1)`, `ypkg-build(1)`, `package.yml(5)`

https://github.com/solus-project/ypkg


## NOTES

Creative Commons Attribution-ShareAlike 3.0 Unported

 * http://creativecommons.org/licenses/by-sa/3.0/
