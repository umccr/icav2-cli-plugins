## CONFIG SETUP ##

__config_setup.sh

## END CONFIG SETUP ##

## INVOKE PROJECT PIPELINE ##

# No pagination while :; do
eval "$(\
  curl   \
    --fail   \
    --silent   \
    --location   \
    --request 'GET'   \
    --header 'Accept: application/vnd.illumina.v3+json'   \
    --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}"   \
    --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/pipelines" | \
  jq \
    --raw-output \
    --arg cols "$(tput cols)" \
     '
      .items |
      (map(.pipeline.code | length) | max) as $max_pipeline_code |
      (($cols | tonumber) - $max_pipeline_code - 4) as $max_description_length |
      map(
        [
          "printf",
          "%-*s -- %.*s\n",
          $max_pipeline_code, .pipeline.code,
          $max_description_length, "Date=\(.pipeline.timeCreated) Description=\(.pipeline.description)"
        ] |
        @sh
      )
      |
      .[]
    ' \
)"