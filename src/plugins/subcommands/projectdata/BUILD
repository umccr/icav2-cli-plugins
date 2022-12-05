# This target sets the metadata for all the Python non-test files in this directory.
python_sources(
    name="ls",
)

# This target allows us to bundle our app into a PEX binary file via
#  `./pants package`. We can also run it with `./pants run`. See
#  https://www.pantsbuild.org/docs/python-package-goal and
#  https://www.pantsbuild.org/docs/python-run-goal.
pex_binary(
    name="ls_binary",
    entry_point="ls.py",
)

python_distribution(
    name="dist",
    dependencies=[":lib"]
)

