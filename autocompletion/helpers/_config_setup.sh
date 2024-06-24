# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi
