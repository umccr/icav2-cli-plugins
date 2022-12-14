if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"