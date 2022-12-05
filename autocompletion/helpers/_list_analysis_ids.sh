## CONFIG SETUP ##

__config_setup.sh

## END CONFIG SETUP ##

## LIST ANALYSIS IDS

curl \
  --fail --silent --location \
  --request 'GET' \
  --header 'Accept: application/vnd.illumina.v3+json' \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/analyses" | \
jq --raw-output \
  '
   .items |
   map(.id) |
   .[]
  '

