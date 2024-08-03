curl \
  --fail --silent --location \
  --request "GET" \
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects?includeHiddenProjects=false&pageSize=100" \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" | \
jq \
  --raw-output \
  --arg attribute_name "${ATTRIBUTE_NAME}" \
  '
    .items |
    map(.[$attribute_name]) |
    .[]
  '