curl 'https://api.sarvam.ai/speech-to-text/job/v1' \
  -H 'accept: */*' \
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuYW1hbkBzYXJ2YW0uYWkiLCJlbWFpbCI6Im5hbWFuQHNhcnZhbS5haSIsIm5hbWUiOiJOYW1hbiBKYWluIiwic3NvX3Byb3ZpZGVyIjoiZ29vZ2xlIiwiYXVkIjpbImFwaS1kYXNoYm9hcmQiXSwiaWF0IjoxNzcxMDc0NTk5LCJleHAiOjE3NzEwNzU0OTksInR5cGUiOiJkYXNoYm9hcmQifQ.nfFGzlOQAdz_T1WsV-ZVoGrvwHQ87s5HxGVdm9SZ6L0dCj5m7KoukPsuUesGWcQMsIcGAGUshY-8pxDkYmzNpfQ2hgg0VsFuWEM9u3e5h2V6nrPlf3SLdYZBqnQ6JO6VRyJDOJVrqVLclgdu5oasHn-3vmsTsVjd7DQ57xmRjJB1AfqVpT6G1cw5vPR8fuGx8g7ZcZVYt_UETSAtBgxtBo8Ijx50cYnewG4wQE05Tnq7O5crRyPI7iFVUd7kRherjVJGU3u-eu-S8JYRVv1OwwXRhocI4MWj8YxdVDsi18NQivqyg02AzcmiX7tDZ4eJK-ikLuiUmtDm46CUgGl6FQ' \
  -H 'content-type: application/json' \
  -H 'origin: https://dashboard.sarvam.ai' \
  -H 'priority: u=1, i' \
  -H 'referer: https://dashboard.sarvam.ai/' \
  -H 'sec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36' \
  --data-raw '{"job_parameters":{"language_code":"unknown","model":"saaras:v3","mode":"transcribe","with_timestamps":false,"with_diarization":false,"num_speakers":null,"input_audio_codec":null}}'


  --------

  curl 'https://api.sarvam.ai/speech-to-text/job/v1/upload-files' \
  -H 'accept: */*' \
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuYW1hbkBzYXJ2YW0uYWkiLCJlbWFpbCI6Im5hbWFuQHNhcnZhbS5haSIsIm5hbWUiOiJOYW1hbiBKYWluIiwic3NvX3Byb3ZpZGVyIjoiZ29vZ2xlIiwiYXVkIjpbImFwaS1kYXNoYm9hcmQiXSwiaWF0IjoxNzcxMDc0NTk5LCJleHAiOjE3NzEwNzU0OTksInR5cGUiOiJkYXNoYm9hcmQifQ.nfFGzlOQAdz_T1WsV-ZVoGrvwHQ87s5HxGVdm9SZ6L0dCj5m7KoukPsuUesGWcQMsIcGAGUshY-8pxDkYmzNpfQ2hgg0VsFuWEM9u3e5h2V6nrPlf3SLdYZBqnQ6JO6VRyJDOJVrqVLclgdu5oasHn-3vmsTsVjd7DQ57xmRjJB1AfqVpT6G1cw5vPR8fuGx8g7ZcZVYt_UETSAtBgxtBo8Ijx50cYnewG4wQE05Tnq7O5crRyPI7iFVUd7kRherjVJGU3u-eu-S8JYRVv1OwwXRhocI4MWj8YxdVDsi18NQivqyg02AzcmiX7tDZ4eJK-ikLuiUmtDm46CUgGl6FQ' \
  -H 'content-type: application/json' \
  -H 'origin: https://dashboard.sarvam.ai' \
  -H 'priority: u=1, i' \
  -H 'referer: https://dashboard.sarvam.ai/' \
  -H 'sec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36' \
  --data-raw '{"job_id":"20260214_41391875-8042-4f11-a9e5-91552d9e29ac","files":["10000.mp3"]}'


  -------


  curl 'https://appsprodpublicsa.blob.core.windows.net/bulk-upload-storage/jobs/2026-02-14/SPEECH_TO_TEXT_BULK/41391875-8042-4f11-a9e5-91552d9e29ac/inputs/10000.mp3?se=2026-02-14T14%3A09%3A59Z&sp=w&sv=2025-05-05&sr=b&sig=xwvB0YIkfF2eFSTzPB7epTfpRwgD0UIjA5haYQNAang%3D' \
  -X 'PUT' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'Connection: keep-alive' \
  -H 'Content-Length: 80809' \
  -H 'Content-Type: audio/mpeg' \
  -H 'Origin: https://dashboard.sarvam.ai' \
  -H 'Referer: https://dashboard.sarvam.ai/' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: cross-site' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'x-ms-blob-type: BlockBlob'


  --------


  curl 'https://api.sarvam.ai/speech-to-text/job/v1/20260214_41391875-8042-4f11-a9e5-91552d9e29ac/start' \
  -H 'accept: */*' \
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuYW1hbkBzYXJ2YW0uYWkiLCJlbWFpbCI6Im5hbWFuQHNhcnZhbS5haSIsIm5hbWUiOiJOYW1hbiBKYWluIiwic3NvX3Byb3ZpZGVyIjoiZ29vZ2xlIiwiYXVkIjpbImFwaS1kYXNoYm9hcmQiXSwiaWF0IjoxNzcxMDc0NTk5LCJleHAiOjE3NzEwNzU0OTksInR5cGUiOiJkYXNoYm9hcmQifQ.nfFGzlOQAdz_T1WsV-ZVoGrvwHQ87s5HxGVdm9SZ6L0dCj5m7KoukPsuUesGWcQMsIcGAGUshY-8pxDkYmzNpfQ2hgg0VsFuWEM9u3e5h2V6nrPlf3SLdYZBqnQ6JO6VRyJDOJVrqVLclgdu5oasHn-3vmsTsVjd7DQ57xmRjJB1AfqVpT6G1cw5vPR8fuGx8g7ZcZVYt_UETSAtBgxtBo8Ijx50cYnewG4wQE05Tnq7O5crRyPI7iFVUd7kRherjVJGU3u-eu-S8JYRVv1OwwXRhocI4MWj8YxdVDsi18NQivqyg02AzcmiX7tDZ4eJK-ikLuiUmtDm46CUgGl6FQ' \
  -H 'content-type: application/json' \
  -H 'origin: https://dashboard.sarvam.ai' \
  -H 'priority: u=1, i' \
  -H 'referer: https://dashboard.sarvam.ai/' \
  -H 'sec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36' \
  -H 'x-dashboard: true' \
  --data-raw '{"job_id":"20260214_41391875-8042-4f11-a9e5-91552d9e29ac","job_parameters":{"language_code":"unknown","model":"saaras:v3","mode":"transcribe","with_diarization":false,"with_timestamps":false}}'

  ----------


  curl 'https://api.sarvam.ai/speech-to-text/job/v1/20260214_41391875-8042-4f11-a9e5-91552d9e29ac/status' \
  -H 'accept: */*' \
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuYW1hbkBzYXJ2YW0uYWkiLCJlbWFpbCI6Im5hbWFuQHNhcnZhbS5haSIsIm5hbWUiOiJOYW1hbiBKYWluIiwic3NvX3Byb3ZpZGVyIjoiZ29vZ2xlIiwiYXVkIjpbImFwaS1kYXNoYm9hcmQiXSwiaWF0IjoxNzcxMDc0NTk5LCJleHAiOjE3NzEwNzU0OTksInR5cGUiOiJkYXNoYm9hcmQifQ.nfFGzlOQAdz_T1WsV-ZVoGrvwHQ87s5HxGVdm9SZ6L0dCj5m7KoukPsuUesGWcQMsIcGAGUshY-8pxDkYmzNpfQ2hgg0VsFuWEM9u3e5h2V6nrPlf3SLdYZBqnQ6JO6VRyJDOJVrqVLclgdu5oasHn-3vmsTsVjd7DQ57xmRjJB1AfqVpT6G1cw5vPR8fuGx8g7ZcZVYt_UETSAtBgxtBo8Ijx50cYnewG4wQE05Tnq7O5crRyPI7iFVUd7kRherjVJGU3u-eu-S8JYRVv1OwwXRhocI4MWj8YxdVDsi18NQivqyg02AzcmiX7tDZ4eJK-ikLuiUmtDm46CUgGl6FQ' \
  -H 'content-type: application/json' \
  -H 'origin: https://dashboard.sarvam.ai' \
  -H 'priority: u=1, i' \
  -H 'referer: https://dashboard.sarvam.ai/' \
  -H 'sec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'


  -----------

  curl 'https://api.sarvam.ai/speech-to-text/job/v1/download-files' \
  -H 'accept: */*' \
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H 'authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuYW1hbkBzYXJ2YW0uYWkiLCJlbWFpbCI6Im5hbWFuQHNhcnZhbS5haSIsIm5hbWUiOiJOYW1hbiBKYWluIiwic3NvX3Byb3ZpZGVyIjoiZ29vZ2xlIiwiYXVkIjpbImFwaS1kYXNoYm9hcmQiXSwiaWF0IjoxNzcxMDc0NTk5LCJleHAiOjE3NzEwNzU0OTksInR5cGUiOiJkYXNoYm9hcmQifQ.nfFGzlOQAdz_T1WsV-ZVoGrvwHQ87s5HxGVdm9SZ6L0dCj5m7KoukPsuUesGWcQMsIcGAGUshY-8pxDkYmzNpfQ2hgg0VsFuWEM9u3e5h2V6nrPlf3SLdYZBqnQ6JO6VRyJDOJVrqVLclgdu5oasHn-3vmsTsVjd7DQ57xmRjJB1AfqVpT6G1cw5vPR8fuGx8g7ZcZVYt_UETSAtBgxtBo8Ijx50cYnewG4wQE05Tnq7O5crRyPI7iFVUd7kRherjVJGU3u-eu-S8JYRVv1OwwXRhocI4MWj8YxdVDsi18NQivqyg02AzcmiX7tDZ4eJK-ikLuiUmtDm46CUgGl6FQ' \
  -H 'content-type: application/json' \
  -H 'origin: https://dashboard.sarvam.ai' \
  -H 'priority: u=1, i' \
  -H 'referer: https://dashboard.sarvam.ai/' \
  -H 'sec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36' \
  --data-raw '{"job_id":"20260214_41391875-8042-4f11-a9e5-91552d9e29ac","files":["0.json"]}'