curl \
  --fail --silent --location \
  --request "GET" \
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/" \
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