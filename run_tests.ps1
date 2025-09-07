docker compose up --build test-runner
docker cp test-runner:/app/coverage.xml ./coverage.xml
docker compose rm -f test-runner