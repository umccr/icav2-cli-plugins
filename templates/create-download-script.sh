#!/usr/bin/env bash

# Set to fail
set -euo pipefail

# Globals
IS_ENCRYPTED="<__IS_ENCRYPTED__>"
KEYBASE_USERNAME="<__KEYBASE_USERNAME__>"
SCRIPT_EXPIRY_EPOCH="<__EXPIRY_DATE_EPOCH__>"

# Keybase encryption
# absolutelyencrypted="$( \
#   keybase encrypt --infile /dev/stdin --outfile /dev/stdout <KEYBASE_USERNAME> --binary <<< "absolutelyencrypted!" | \
#   "$(get_base64_binary)" --wrap=0 \
# )"
# keybase team list-memberships --json | jq '.teams | map(.fq_name)'
  #[
  #  "vccc.umccr.admin"
  #]

# Keybase decryption
# base64 --decode <<< "${absolutelyencrypted}" | \
# keybase decrypt --infile /dev/stdin --outfile /dev/stdout 2>/dev/null


# Openssl decryption

# Openssl encryption

# Functions
# Write to stderr
echo_stderr(){
  echo "$(date --iso-8601=seconds):" "$@" 1>&2
}

# Print Usage
print_usage(){
  echo "
icav2-download-script-<__NAME__>-<__DATE__>.sh (--download-path </path/to/local/directory)
                                               [--private-key </path/to/private_key> | --keybase]
                                               [--num-parallel-jobs]
                                               [--skip-checksum]
                                               [--decompress-ora]
                                               [--orad-threads-per-job <number>]
                                               [--help]

Description:
Download <__NAME__> data from ICAv2, this script expires on <__EXPIRY_DATE__>.

Please ensure you have <__REQUIRED_DISK_SPACE__> available on your destination drive.

Options:
  -d | --download-path:        Path to download data to, note the parent of this directory must exist.
                               A trailing slash on this parameter value will have no affect on the download directory structure.
                               Given a relative subdirectory path is foo/ with file bar.txt and a --download-path value of 'hop/skip/jump', the
                               file bar.txt will be downloaded to hop/skip/jump/foo/bar.txt.
  -p | --private-key:          Path to private key, used to decrypt data
  --keybase:                   Use keybase to decrypt data.
                               (Note please specify one and only one of --keybase and --private-key)
  -j | --num-parallel-jobs:    Number of parallel downloads,
                               You may also provide a percentage (75%) which spawns <pct> * Num System CPUs (Default '75%')
  -s | --skip-checksum:        Do not calculate the etag value of the local file to compare to the source etag.
  --decompress-ora:            Decompress ORA files as they come in
  --orad-threads-per-job:      Number of threads to use per job to decompress ora files
  --help:                      Print this message
"
}

# Decrypt presigned url
decrypt_presigned_url_with_openssl(){
  : '
  Use openssl to decrypt a presigned url with a private key
  Return the presigned url decrypted
  '
  local encrypted_presigned_url="$1"
  local private_key="$2"

  "$(get_base64_binary)" --decode "${encrypted_presigned_url}" | \
  openssl pkeyutl \
    -decrypt \
    -inkey "${private_key}" \
    -keyform "PEM"
}

decrypt_presigned_url_with_keybase(){
  : '
  Use keybase to decrypt a presigned url
  '
  local encrypted_presigned_url="$1"
  "$(get_base64_binary)" --decode <<< "${encrypted_presigned_url}" | \
  keybase decrypt \
    --infile /dev/stdin \
    --outfile /dev/stdout 2>/dev/null
}

remove_presigned_url_credentials_for_logs(){
  : '
  Given a presigned url
  Convert to a regular url
  '
  "$(get_sed_binary)" \
    --regexp-extended \
    --expression 's%(.*)\?(.*)%\1%' <<< "${1}"
}


calculate_block_size(){
  : '
  Calculate the block size based on the following formula
  max(
    1,
    ceil(
      log2(
        max(
          1,
          filesize
        )
      ) - log2(MAX_NUM_BLOCKS)
    )
  ) * 2^23

  Essentially files less than 64 Gb will have a blocksize of 8Mb,
  files less than 128 Gb will have a blocksize of 16Mb,
  files less than 256 Gb will have a blocksize of 32Mb, etc
  '

  local file_size="$1"
  local num_parts="$2"

  python3 - <<EOF
#!/usr/bin/env python3

"""
Print the expected block size and confirm this matches the number of parts in the etag
"""

from math import log2, ceil, pow
from sys import stderr, exit
MAX_NUM_BLOCKS=pow(2, 13)
MIN_BLOCK_SIZE=pow(2, 23)

NUM_PARTS=${num_parts}
FILE_SIZE=${file_size}

block_size_exponent=int(
  max(
    # Default block size
    log2(MIN_BLOCK_SIZE),
    # Otherwise get the ceiling of
    # filesize / max-num-blocks then logged in base2
    # Note log2(a/b) is the same as log2(a) - log2(b)
    ceil(
      log2(
        max(
          1,
          FILE_SIZE
        )
      ) -
      log2(MAX_NUM_BLOCKS)
    )
  )
)
block_size=int(pow(2, block_size_exponent))

if FILE_SIZE < block_size*(NUM_PARTS-1) or block_size*NUM_PARTS < FILE_SIZE:
   print(f"Error! Block size estimation is incorrect, file size: '{FILE_SIZE}', num blocks '{NUM_PARTS}', estimated block size '{block_size}'", file=stderr)
   print(f"Error! Given block size of '{block_size}' would expect '{ceil(FILE_SIZE/block_size)}' blocks")
   exit(1)
else:
  print(block_size)
EOF

}

# Check / compare etag
compute_local_etag(){
  : '
  Compute the local etag of the file
  Credit: https://gist.github.com/emersonf/7413337
  '
  local file_path="$1"
  local block_size_mb="$2"
  local num_parts="$3"

  # Additional local variables
  local num_parts
  local part_iter

  # Check how many parts, we may just need to return the md5sum
  if [[ "${num_parts}" == "1" ]]; then
    "$(get_md5sum_binary)" "${file_path}" | cut -d' ' -f1
    return 0
  fi

  # Otherwise we need to go this in multiple checks
  checksum_file="$("$(get_mktemp_binary)" -t "checksum_file.$(basename "${file_path}").XXX")"

  # Set iter
  part_iter=0

  # Start loop
  while [[ "${part_iter}" -lt "${num_parts}" ]]; do
    # Sections we've already done
    skip="$((block_size_mb * part_iter))"
    "$(get_dd_binary)" \
      bs="$(python3 -c "from math import pow; print(int(pow(2,20)))")" \
      count="${block_size_mb}" \
      skip="${skip}" \
      if="${file_path}" 2>/dev/null | \
    "$(get_md5sum_binary)" >> "${checksum_file}"

    # Iterate
    part_iter="$((part_iter + 1))"
  done

  # Calculate and 'return' etag
  echo "$(xxd --revert --plain "${checksum_file}" | "$(get_md5sum_binary)")-${num_parts}" | \
  "$(get_sed_binary)" 's%  --%-%'
}


# Download file to path (main function to parallelise)
# Export this function
download_presigned_url(){
  : '
  Download a presigned url to a path
  '
  # Inputs
  local presigned_url="$1"
  local local_path="$2"
  local private_key_path="$3"
  local source_etag="$4"
  local source_filesize="$5"
  local is_encrypted="$6"
  local skip_checksum="$7"
  local decompress_ora="$8"
  local orad_threads_per_job="$9"

  # Local vars
  local local_etag
  local block_size_mb

  # Get presigned url if encrypted
  if [[ "${is_encrypted}" == "true" ]]; then
      if [[ "${use_keybase}" == "true" ]]; then
        presigned_url="$( \
          decrypt_presigned_url_with_keybase "${presigned_url}" \
        )"
      else
        presigned_url="$( \
          decrypt_presigned_url_with_openssl "${presigned_url}" "${private_key_path}" \
        )"
      fi
  fi

  # Check local path
  mkdir -p "$(dirname "${local_path}")"

  # Download file
  echo_stderr "Downloading '$(remove_presigned_url_credentials_for_logs "${presigned_url}")' to '${local_path}' (size: ${source_filesize})"
  curl --fail --silent --location --show-error \
    --output "${local_path}" \
    "${presigned_url}"
  echo_stderr "Download of '$(remove_presigned_url_credentials_for_logs "${presigned_url}")' to '${local_path}' (size: ${source_filesize}) complete"

  # Skip checksum
  if [[ "${skip_checksum}" == "false" ]]; then
    echo_stderr "Calculating local etag"

    # Get num parts from etag
    num_parts="$( \
      if [[ "${source_etag}" =~ .*"-".* ]]; then \
        "$(get_sed_binary)" \
          --regexp-extended \
          --expression 's%.*\-([0-9]+)%\1%' <<< "${source_etag}"; \
      else
        echo "1";
      fi \
    )"

    # Get block size
    block_size_mb="$( \
      calculate_block_size "${source_filesize}" "${num_parts}"
    )"

    # Get local etag
    local_etag="$( \
      compute_local_etag "${local_path}" "${block_size_mb}" "${num_parts}"
    )"

    # Compare local etag to source etag
    if [[ "${local_etag}" != "${source_etag}" ]]; then
      echo_stderr "Error! Invalid eTag calculated for file '${local_path}', got source etag '${source_etag}' but local etag '${local_etag}'"
      return 1
    else
      echo_stderr "File '${local_path}' checksum is complete"
    fi
  fi

  # Decompress ora
  if [[ "${decompress_ora}" == "true" ]]; then
    if [[ "${local_path}" == *.ora ]]; then
      echo_stderr "Local path '${local_path}' is an ora file and --decompress-ora is set to true, decompressing '${local_path}'"
      orad --gz \
        --threads "${orad_threads_per_job-1}" \
        --quiet \
        --force
      echo_stderr "'${local_path}' has been decompressed to '${local_path%.ora}.gz'"
      if [[ "${remove_ora_files_after_decompression}" == "true" ]]; then
        echo_stderr "Deleting '${local_path}'"
        rm "${local_path}"
      fi
    fi
  fi
}

download_presigned_url_from_base64_jq_string(){
  : '
  Decode base64 into jq object, which should contain the following attributes
  {
    "presigned_url": "https://...",
    "path": foo/bar/x,
    "file_size": 12345678,
    "etag": "abcdefg-1234"
  }
  '
  # Inputs
  local base64_string="$1"

  local json_str
  local presigned_url
  local dest_path
  local source_etag
  local source_file_size

  json_str="$( \
    "$(get_base64_binary)" --decode <<< "${base64_string}" | \
    jq --raw-output
  )"

  presigned_url="$( \
    jq --raw-output \
      '.presigned_url' <<< "${json_str}"
  )"

  dest_path="${download_path%/}/$( \
    jq --raw-output \
      '.path' <<< "${json_str}"
  )"

  source_etag="$( \
    jq --raw-output \
      '.etag' <<< "${json_str}"
  )"

  source_file_size="$( \
    jq --raw-output \
      '.file_size' <<< "${json_str}"
  )"

  # Downloading presigned url
  download_presigned_url \
    "${presigned_url}" \
    "${dest_path}" \
    "${private_key_path}" \
    "${source_etag}" \
    "${source_file_size}" \
    "${IS_ENCRYPTED}" \
    "${skip_checksum}" \
    "${decompress_ora}" \
    "${orad_threads_per_job}"

}

# Check / set binaries
get_md5sum_binary(){
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    echo "gmd5sum"
  else
    echo "md5sum"
  fi
}

get_mktemp_binary(){
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    echo "gmktemp"
  else
    echo "mktemp"
  fi
}

get_sed_binary(){
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    echo "gsed"
  else
    echo "sed"
  fi
}

get_base64_binary(){
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    echo "gbase64"
  else
    echo "base64"
  fi
}

get_dd_binary(){
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    echo "gdd"
  else
    echo "dd"
  fi
}

get_date_binary(){
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    echo "gdate"
  else
    echo "date"
  fi
}

check_binaries(){
  : '
  Make sure that binaries used in script exist in PATH
  '
  if ! (type \
          jq \
          curl \
          parallel \
          xxd \
          python3 \
          get_md5sum_binary \
          get_mktemp_binary \
          get_sed_binary \
          get_base64_binary \
          xxd 1>/dev/null); then
    return 1
  fi
}

check_keybase_binary() {
  : '
  Make sure that keybase is installed
  '
  if ! type keybase 1>/dev/null; then
    return 1
  fi
}


# Check expiry
if [[ "$("$(get_date_binary)" +%s)" -gt "${SCRIPT_EXPIRY_EPOCH}" ]]; then
  echo_stderr "This script has expired, all of the presigned urls are out of date!"
  exit 1
fi

# Check bash version

# Get arguments
remove_ora_files_after_decompression="false"
download_path=""
private_key_path=""
private_key="false"
use_keybase="false"
num_parallel_jobs="75%"
skip_checksum="false"
decompress_ora="false"
orad_threads_per_job="1"

# Get args from command line
while [ $# -gt 0 ]; do
  case "$1" in
    -d | --download-path)
      download_path="$2"
      shift 1
      ;;
    -p | --private-key)
      private_key_path="$2"
      private_key="true"
      shift 1
      ;;
    --keybase)
      use_keybase="true"
      ;;
    -n | --num-parallel-jobs)
      num_parallel_jobs="$2"
      shift 1
      ;;
    -s | --skip-checksum)
      skip_checksum="true"
    ;;
    --decompress-ora)
      decompress_ora="true"
    ;;
    --orad-threads-per-job)
      orad_threads_per_job="$2"
    ;;
    -h | --help)
      print_usage
      exit 0
      ;;
  esac
  shift 1
done

# Check if download path defined
if [[ -z "${download_path-}" ]]; then
  echo_stderr "Error! Please ensure --download-path is set"
  print_usage
  exit 1
fi

# Check if parent download path exists
if [[ ! -d "$(dirname "${download_path}")" ]]; then
  echo_stderr "Error! Parent of --download-path '${download_path}' must exist"
  exit 1
fi

# Ensure download path exists
mkdir -p "${download_path}"

# Check binaries
if ! check_binaries; then
  echo_stderr "Please ensure all required items are installed"
  print_usage
fi

# Check if --keybase option is added,
# If option is true, ensure keybase option is in path
# Check if --private-key option is added, if so check path exists?
if [[ "${use_keybase}" == "true" && "${private_key}" == "true" ]]; then
  echo_stderr "Please specify only one of --private-key and --keybase"
  exit 1
fi

# Check encryption is added if data is encrypted
if [[ ( "${use_keybase}" == "true" || "${private_key}" == "true" ) && "${IS_ENCRYPTED}" == "false" ]]; then
  echo_stderr "Private key or keybase specified but data is not encrypted so ignoring"
elif [[ ( "${use_keybase}" == "false" && "${private_key}" == "false" ) && "${IS_ENCRYPTED}" == "true" ]]; then
  echo_stderr "Data is encrypted so user must specify one of --keybase or --private-key to decrypt data"
  exit 1
fi

# Check if keybase specified and user is in team name
if [[ "${use_keybase}" == "true" ]]; then
  echo_stderr "--keybase specified, doing some checks"
  if ! check_keybase_binary; then
    echo_stderr "Couldn't find keybase in users PATH"
  fi
  keybase_status_json_str="$( \
    keybase status --json \
  )"

  if [[ ! "$(jq --raw-output '.LoggedIn' <<< "${keybase_status_json_str}")" == "true" ]]; then
    echo_stderr "--keybase specified but user not logged into keybase, exiting"
    exit 1
  fi

  if [[ ! "$(jq --raw-output '.SessionIsValid' <<< "${keybase_status_json_str}")" == "true" ]]; then
    echo_stderr "--keybase specified but is an invalid session, please log in again"
    exit 1
  fi

  keybase_in_team="$( \
    keybase team list-memberships --json | \
    jq --arg keybase_teamname "${KEYBASE_USERNAME}" \
      '
        .teams |
        map(
          select(.fq_name == $keybase_teamname)
        ) |
        length
      '
  )"
  keybase_user="$( \
    jq --raw-output '.Username' <<< "${keybase_status_json_str}"
  )"

  # Check were logged in to the right account
  if [[ "${keybase_in_team}" == "0" && ! "${KEYBASE_USERNAME}" == "${keybase_user}" ]]; then
    echo_stderr "Expected '${KEYBASE_USERNAME}' as either a team or username for keybase user '${keybase_user}'"
  fi

fi

# Check orad binary is in path if --decompress-ora is true
if [[ "${decompress_ora}" == "true" ]] && type orad 1>/dev/null 2>&1; then
  echo_stderr "Error! Could not find orad in path but --decompress-ora parameter is set to true"
fi


# Convert jq input to bash array and run parallel over array for each download function
# Where jq input contains a path, etag and presigned url
PRESIGNED_URL_BASE64_ARRAY=( \
<__PRESIGNED_URL_BASE64_ARRAY_JQ_LIST__>
)

# Export functions for parallel
export -f echo_stderr
export -f print_usage
export -f decrypt_presigned_url_with_openssl
export -f decrypt_presigned_url_with_keybase
export -f remove_presigned_url_credentials_for_logs
export -f calculate_block_size
export -f compute_local_etag
export -f download_presigned_url
export -f download_presigned_url_from_base64_jq_string
export -f get_md5sum_binary
export -f get_mktemp_binary
export -f get_sed_binary
export -f get_base64_binary
export -f get_dd_binary

# Export vars for parallel
export IS_ENCRYPTED
export skip_checksum
export decompress_ora
export orad_threads_per_job
export download_path
export use_keybase
export private_key_path

# Run download in parallel
parallel \
  --jobs "${num_parallel_jobs}" \
  download_presigned_url_from_base64_jq_string ::: "${PRESIGNED_URL_BASE64_ARRAY[@]}"
