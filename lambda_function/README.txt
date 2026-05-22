Lambda front-end for the Vacation Planner AgentCore runtime (qualifier: vacation_planner).

When invoking AgentCore, the function passes traceId with Sampled=1 so CloudWatch traces are not suppressed by Lambda's default unsampled X-Ray context.

Redeploy this function after code changes for traces/API Gateway to pick them up.
