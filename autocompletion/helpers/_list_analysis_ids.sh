## CONFIG SETUP ##

__config_setup.sh

## END CONFIG SETUP ##

## LIST ANALYSIS IDS
page_offset=0
page_size=1000
total_item_count="$( \
  curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=0&pageSize=1" | \
  jq --raw-output '.totalItemCount' \
)"

while :; do
  eval "$( \
    curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=${page_offset}&pageSize=${page_size}&sort=startDate%20desc" | \
    jq --raw-output \
      --arg cols "$(tput cols)" \
      '
        .items |
        (map(.id | length) | max) as $max_id_length |
        (($cols | tonumber) - $max_id_length - 4) as $max_description_length |
        map(
          [
            "printf",
            "%-*s -- %.*s\n",
            $max_id_length, .id,
            $max_description_length, "UserRef: \(.userReference)  Date: \(.startDate)"
          ] |
          @sh
        ) |
        .[]
      '
  )"
    (( page_offset += page_size ))

    if ! (( page_offset < total_item_count )); then
      break
    fi
done

