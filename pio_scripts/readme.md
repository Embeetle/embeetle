# PIO SCRIPTS

## Summary

This script bridges the Source Analyzer with PlatformIO's build system. It works
in two phases:

1. Extract build information via dry-run
2. Apply filtering to exclude unwanted files/directories

To apply the filtering, this script modifies the project's platformio.ini and
inserts PRE-scripts. Any build the user then invokes with the usual `pio run`
command will be filtered.

```
          dry-run output
   ┌─────────────<─────────────────┐
   │                               │
┌──┴───┐                      ┌────┴──────┐
│  SA  │─────────>────────────│ SA Bridge │─────> Ensure the project only
└──────┘  list files/hdirs    └───────────┘       builds relevant files
          to be excluded                          (and includes relevant
                                                  hdirs)
```

> @Johan:
> This `sa_bridge.py` is the only script you'll ever need for your SA to
> interact with a PlatformIO project.
> You no longer have to worry about the intricacies of the PlatformIO build
> system to make it skip certain files/hdirs.


## How to use the Script

To use `sa_bridge.py` you have two options:

1) Import it as a python module and call its two convenience functions:
    - store_dry_run_output(..)
    - apply_build_filters(..)

2) Use it as a standalone script which you launch with certain arguments.


## Further Documentation

For more details, please launch the script with the `--help` flag. It shows an
extensive help doc with precise instructions on how to use the script in the two
scenarios (import module or standalone script).