export AWS_REGION=us-west-2

export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/vacation-planner
export AGENT_RUNTIME_ID=vacation_planner-kqdG1OFLan
export AGENTCORE_IMAGE_TAG=f243386
export ROLE_ARN=arn:aws:iam::850652371396:role/YOUR_AGENTCORE_EXECUTION_ROLE
export SERPER_API_KEY=[This is the Serper API key that is used to access the Serper API]
aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id vacation_planner-kqdG1OFLan \
  --agent-runtime-artifact '{"containerConfiguration":{"containerUri":"$ECR_URI:$AGENTCORE_IMAGE_TAG"}}' \
  --role-arn $ROLE_ARN \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --environment-variables '{"SERPER_API_KEY":"$SERPER_API_KEY"}' \
  --region us-west-2


  # in the CI/CD pipeline, we will need to update the Serper API key from the environment variable

  # Notes: You can also update the Serper API key in the AgentCore / Runtime / Update hosting, then 
  # add the environment variable.