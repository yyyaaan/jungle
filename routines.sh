endpoint="http://127.0.0.1:8000/ycrawl"

echo "Start a new day"
curl -d '{"role": "test"}' -H "Content-Type: application/json" -H "Authorization: Bearer $token" -X POST $endpoint/joblist/start/

echo "Checkin"
curl -H "Authorization: Bearer $token" -X POST $endpoint/joblist/checkin/
