curl \
  --fail --silent --location \
  --request "GET" \
  --url "https://ica.illumina.com/ica/rest/api/projects/${ICAV2_PROJECT_ID}/pipelines" \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" | \
jq \
  --raw-output \
  --arg attribute_type "${ATTRIBUTE_NAME}" \
  '
    .items |
    map(.pipeline | .[$attribute_type]) |
    .[]
  '