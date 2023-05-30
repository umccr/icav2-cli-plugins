## CONFIG SETUP ##

__config_setup.sh

## END CONFIG SETUP ##
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
    --arg cols "$(tput cols)"\
     '
      .items |
      (map(.pipeline.id | length) | max) as $max_pipeline_id |
      (($cols | tonumber) - $max_pipeline_id - 4) as $max_description_length |
      map(
        [
          "printf",
          "%-*s -- %.*s\n",
          $max_pipeline_id, .pipeline.id,
          $max_description_length, "Code: \(.pipeline.code) Date: \(.pipeline.timeCreated) Description: \(.pipeline.description)"
        ] |
        @sh
      )
      |
      .[]
    ' \
)"
