docker buildx build --platform linux/arm64 \
  -t vacation-planner:$(git rev-parse --short HEAD) \
  -t vacation-planner:latest \
  --load .