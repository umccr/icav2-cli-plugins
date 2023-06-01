
max_items=1000
parent_folder_path="/"
if [[ -n "${CURRENT_WORD-}" ]]; then
  if [[ "${CURRENT_WORD}" =~ ^.*/$ ]]; then
    parent_folder_path="${CURRENT_WORD}"
    basename_var=""
  else
    parent_folder_path="$(dirname "${CURRENT_WORD}")/"
    if [[ "${parent_folder_path}" == "//" ]]; then
      parent_folder_path="/"
    fi
    basename_var="$(basename "${CURRENT_WORD}")"
  fi
fi

params="$( \
  jq --null-input --raw-output \
    --arg parent_folder_path "${parent_folder_path}" \
    --arg file_name "${basename_var}" \
    --arg type "${ITEM_TYPE-}" \
    --arg page_size "${max_items}" \
    '
      # Intialise parameters
      {
        "parentFolderPath": $parent_folder_path,
        "filename": $file_name,
        "filenameMatchMode": "FUZZY",
        "pageSize": $page_size,
        "type": $type
      } |
      # Drop nulls
      with_entries(
        select(
          .value != ""
        )
      ) |
      # Convert to string
      to_entries |
      map(
        "\(.key)=\(.value)"
      ) |
      join("&")
    '
)"

# List Data in Directory
curl \
  --fail --silent --location \
  --request GET \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    sort_by(.data.details.path | ascii_downcase) |
    map(
      .data.details.path
    ) |
    .[]
  '
