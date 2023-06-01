## CONFIG SETUP ##

__config_setup.sh

## END CONFIG SETUP ##

eval "$(\
  curl \
  --fail --silent --location \
  --request "GET" \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/" | \
  jq \
    --raw-output \
    --arg cols "$(tput cols)"\
     '
      .items |
      (map(.id | length) | max) as $max_project_id_length |
      (($cols | tonumber) - $max_project_id_length - 4) as $max_project_name_length |
      map(
        [
          "printf",
          "%-*s -- %.*s\n",
          $max_project_id_length, .id,
          $max_project_name_length, .name
        ] |
        @sh
      )
      |
      .[]
    ' \
)"