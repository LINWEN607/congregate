#!/usr/bin/env bash
poetry run pylint congregate | tee pylint.txt || poetry run pylint-exit $?
export score=$(sed -n 's/^Your code has been rated at \([-0-9.]*\)\/.*/\1/p' pylint.txt)
echo "Pylint score was ${score}"
export json_badge_info=$(curl -H "PRIVATE-TOKEN:$ACCESS_TOKEN" -X GET https://gitlab.com/api/v4/projects/$CI_PROJECT_ID/badges)
echo ${json_badge_info}
#"pylint_badge_id=$(expr $json_badge_info : '.*\"id\":\([0-9]*\)')"
[[ $json_badge_info =~ \"id\":([0-9]*) ]]
export pylint_badge_id=${BASH_REMATCH[1]}
echo ${pylint_badge_id}
export badge_url=https://img.shields.io/badge/lint%20score-$score-blue.svg
curl https://gitlab.com/api/v4/projects/$CI_PROJECT_ID/badges/${pylint_badge_id} -X PUT -H "PRIVATE-TOKEN: $ACCESS_TOKEN" -H "Content-Type: application/json" -d '{"image_url": "'"$badge_url"'"}'
