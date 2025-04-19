import pulumi
import pulumi_aws as aws
import json
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

dynamodb_table = aws.dynamodb.Table(
    "parkingRecords",
    attributes=[
        aws.dynamodb.TableAttributeArgs(
            name="PK",
            type="S"
        )
    ],
    hash_key="PK",
    billing_mode="PAY_PER_REQUEST",
    tags={
        "Environment": "dev",
        "Name": "parking-records"
    }
)


lambda_role = aws.iam.Role(
    "lambdaRole",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }]
    })
)


dynamodb_policy = aws.iam.Policy(
    "dynamodbPolicy",
    description="Policy for Lambda functions to access DynamoDB",
    policy=dynamodb_table.arn.apply(lambda arn: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:UpdateItem",
                "dynamodb:Scan"
            ],
            "Resource": arn
        }]
    }))
)

logs_policy = aws.iam.Policy(
    "logsPolicy",
    description="Policy for Lambda functions to write logs",
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }]
    })
)


aws.iam.RolePolicyAttachment(
    "lambdaBasicExecution",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
)

aws.iam.RolePolicyAttachment(
    "lambdaDynamoDBPolicy",
    role=lambda_role.name,
    policy_arn=dynamodb_policy.arn
)

aws.iam.RolePolicyAttachment(
    "lambdaLogsPolicy",
    role=lambda_role.name,
    policy_arn=logs_policy.arn
)


def create_layer(name: str, path: str) -> aws.lambda_.LayerVersion:
    return aws.lambda_.LayerVersion(
        f"{name}Layer",
        layer_name=name,
        compatible_runtimes=["python3.9"],
        code=pulumi.FileArchive(os.path.join(project_root, "functions", "layers", path))
    )


entry_layer = create_layer(
    "entryDependencies",
    "entry_dependencies"
)
exit_layer = create_layer(
    "exitDependencies",
    "exit_dependencies"
)


def create_lambda_function(
    name: str,
    handler: str,
    layer: aws.lambda_.LayerVersion
) -> aws.lambda_.Function:
    function_dir = os.path.join(project_root, "functions", name)
    utils_dir = os.path.join(project_root, "functions", "utils")
    
    return aws.lambda_.Function(
        name,
        runtime="python3.9",
        handler=handler,
        role=lambda_role.arn,
        code=pulumi.AssetArchive({
            "app.py": pulumi.FileAsset(os.path.join(function_dir, "app.py")),
            "utils": pulumi.FileArchive(utils_dir)
        }),
        layers=[layer.arn],
        timeout=30,
        memory_size=128,
        environment={
            "variables": {
                "DYNAMODB_TABLE_NAME": dynamodb_table.name
            }
        }
    )


entry_function = create_lambda_function(
    "entry",
    "app.lambda_handler",
    entry_layer
)
exit_function = create_lambda_function(
    "exit",
    "app.lambda_handler",
    exit_layer
)


api = aws.apigateway.RestApi(
    "parkingLotApi",
    description="API for parking lot management system"
)


entry_resource = aws.apigateway.Resource(
    "entryResource",
    rest_api=api.id,
    parent_id=api.root_resource_id,
    path_part="entry"
)
exit_resource = aws.apigateway.Resource(
    "exitResource",
    rest_api=api.id,
    parent_id=api.root_resource_id,
    path_part="exit"
)


def create_api_method(
    name: str,
    resource: aws.apigateway.Resource,
    function: aws.lambda_.Function
) -> aws.apigateway.Integration:
    method = aws.apigateway.Method(
        f"{name}Method",
        rest_api=api.id,
        resource_id=resource.id,
        http_method="POST",
        authorization="NONE"
    )
    integration = aws.apigateway.Integration(
        f"{name}Integration",
        rest_api=api.id,
        resource_id=resource.id,
        http_method=method.http_method,
        integration_http_method="POST",
        type="AWS_PROXY",
        uri=function.invoke_arn
    )
   
    aws.lambda_.Permission(
        f"{name}Permission",
        action="lambda:InvokeFunction",
        function=function.name,
        principal="apigateway.amazonaws.com",
        source_arn=pulumi.Output.all(
            api.execution_arn,
            resource.path
        ).apply(lambda args: f"{args[0]}/*/*{args[1]}")
    )

    options_method = aws.apigateway.Method(
        f"{name}OptionsMethod",
        rest_api=api.id,
        resource_id=resource.id,
        http_method="OPTIONS",
        authorization="NONE"
    )
    
    options_integration = aws.apigateway.Integration(
        f"{name}OptionsIntegration",
        rest_api=api.id,
        resource_id=resource.id,
        http_method=options_method.http_method,
        type="MOCK",
        request_templates={
            "application/json": '{"statusCode": 200}'
        }
    )
    
    aws.apigateway.MethodResponse(
        f"{name}OptionsMethodResponse",
        rest_api=api.id,
        resource_id=resource.id,
        http_method=options_method.http_method,
        status_code="200",
        response_parameters={
            "method.response.header.Access-Control-Allow-Headers": True,
            "method.response.header.Access-Control-Allow-Methods": True,
            "method.response.header.Access-Control-Allow-Origin": True
        }
    )

    aws.apigateway.IntegrationResponse(
        f"{name}OptionsIntegrationResponse",
        rest_api=api.id,
        resource_id=resource.id,
        http_method=options_method.http_method,
        status_code="200",
        response_parameters={
            "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
            "method.response.header.Access-Control-Allow-Methods": "'POST,OPTIONS'",
            "method.response.header.Access-Control-Allow-Origin": "'*'"
        }
    )

    aws.apigateway.MethodResponse(
        f"{name}MethodResponse",
        rest_api=api.id,
        resource_id=resource.id,
        http_method=method.http_method,
        status_code="200",
        response_parameters={
            "method.response.header.Access-Control-Allow-Origin": True
        }
    )
    
    aws.apigateway.IntegrationResponse(
        f"{name}IntegrationResponse",
        rest_api=api.id,
        resource_id=resource.id,
        http_method=method.http_method,
        status_code="200",
        response_parameters={
            "method.response.header.Access-Control-Allow-Origin": "'*'"
        }
    )
    
    return integration


entry_integration = create_api_method("entry", entry_resource, entry_function)
exit_integration = create_api_method("exit", exit_resource, exit_function)

deployment = aws.apigateway.Deployment(
    "apiDeployment",
    rest_api=api.id,
    opts=pulumi.ResourceOptions(
        depends_on=[entry_integration, exit_integration]
    )
)

stage = aws.apigateway.Stage(
    "apiStage",
    deployment=deployment.id,
    rest_api=api.id,
    stage_name="v1",
    variables={
        "lambdaAlias": "v1"
    }
)

pulumi.export(
    "api_url",
    pulumi.Output.concat(
        "https://",
        api.id,
        ".execute-api.",
        aws.get_region().name,
        ".amazonaws.com/v1"
    )
)
pulumi.export("dynamodb_table_name", dynamodb_table.name)
