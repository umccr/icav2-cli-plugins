#!/usr/bin/env bash

: '
Wraps around autocompletion to run the appspec completion command from within the docker container
'

# Set to fail on non-zero exit code
set -euo pipefail

# Globals
AUTOCOMPLETION_DIR="autocompletion"
ICAV2_NAMEROOT="icav2"
TEMPLATE_FILE="specs/${ICAV2_NAMEROOT}.yaml"

# Some 'global' temp files
EVAL_TEMPLATE_TEMPFILE="$(mktemp -p /tmp "my_generated_temp_icav2_autocompletion.XXXXXX.yaml")"
PYTHON_TEMPFILE="$(mktemp -p /tmp "my_generated_python_script.XXXXXX.py")"


cat > "${PYTHON_TEMPFILE}" <<EOF
#!/usr/bin/env python
"""
Edit yaml for each item in helpers
"""
from pathlib import Path
import fileinput
import sys
while True:
  break_next_iter = True
  helper_files = [g_item.name for g_item in Path("helpers").glob("*.sh")]
  INDENTATION = 16
  with fileinput.input(sys.argv[1], inplace=True) as template_h:
      for t_line in template_h:
          print_line_as_is = True
          for helper_file in helper_files:
              if "_%s" % helper_file in t_line.strip():
                  break_next_iter = False
                  print_line_as_is = False
                  # We print the entire helper file (and indent by a magical number)
                  with open(str(Path("helpers") / helper_file), "r") as helper_h:
                      for h_line in helper_h.readlines():
                          print(" " * (INDENTATION - 1), h_line.rstrip())
          if print_line_as_is:
              print(t_line.rstrip())

  if break_next_iter:
    break
EOF


(
  : '
  Run the rest in a subshell
  '

  # Change to autocompletion dir
  cd "${AUTOCOMPLETION_DIR}"

  # Copy over the autocompletion to the temp file
  cp "${TEMPLATE_FILE}" "${EVAL_TEMPLATE_TEMPFILE}"

  # Run auto-generator script on file
  python3 "${PYTHON_TEMPFILE}" "${EVAL_TEMPLATE_TEMPFILE}"

  # Create the bash and zsh dirs
  mkdir -p "bash"
  mkdir -p "zsh"

  # Run the bash completion script
  appspec completion \
    "${EVAL_TEMPLATE_TEMPFILE}" \
    --name "${ICAV2_NAMEROOT}" \
    --bash > "bash/${ICAV2_NAMEROOT}.bash"

  # Dont sort values
  sed --in-place 's%complete -o default -F _icav2 icav2%complete -o default -o nosort -F _icav2 icav2%' "bash/${ICAV2_NAMEROOT}.bash"

  # Run the zsh completion script
  appspec completion \
    "${EVAL_TEMPLATE_TEMPFILE}" \
    --name "${ICAV2_NAMEROOT}" \
    --zsh > "zsh/_${ICAV2_NAMEROOT}"

)

# Delete the 'global' tempfiles
rm "${EVAL_TEMPLATE_TEMPFILE}" "${PYTHON_TEMPFILE}"
