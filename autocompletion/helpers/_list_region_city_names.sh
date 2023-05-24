curl \
  --fail --silent --location \
  --request "GET" \
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/regions/" \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" | \
jq \
  --raw-output \
  '
    .items |
    map(.cityName) |
    .[]
  '