docker run --name vacation-planner-local --rm -p 8080:8080 \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
  -e AWS_DEFAULT_REGION=us-west-2 \
  vacation-planner:latest