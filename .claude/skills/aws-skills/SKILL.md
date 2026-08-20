---
name: aws-skills
description: "Разработка под AWS: CDK, Lambda, serverless, S3. Триггеры: «лямбда», «выложи на s3», «инфраструктура в aws»."
---

# AWS Skills

## Overview

Разработка на AWS: CDK, Lambda, serverless паттерны, инфраструктура как код.

## Аккаунт (плейсхолдеры)

Подставь свои значения из AWS-консоли / IAM. Никогда не хардкодь их в коде — держи в env / Secrets Manager.

- **Account ID:** `YOUR_ACCOUNT_ID` (12 цифр, AWS Console → верхний правый угол)
- **Account Name:** `YOUR_ACCOUNT_ALIAS`
- **Region:** `YOUR_REGION` (например `us-east-1`, `eu-central-1`, `us-east-1`)
- **IAM User:** `YOUR_IAM_USER` (выдавай least-privilege политику под задачу)

### S3 Buckets (пример)

| Bucket | Назначение |
|--------|------------|
| `your-backups-bucket` | Автобэкапы (PostgreSQL, MongoDB, Redis, configs) |

### Backup System (пример паттерна)
- **Расписание:** каждые N часов (cron)
- **Хранение:** retention с автоочисткой (например 7 дней)
- **Скрипт:** свой `s3_backup.sh` на сервере

### Credentials
```bash
# Ключи храни в env / профиле AWS CLI, НЕ в коде.
# Переменные: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
# Ещё лучше — IAM Role / SSO вместо long-lived ключей.
```

## When to Use

- Создание AWS инфраструктуры
- Serverless приложения
- Lambda функции
- API Gateway + DynamoDB
- CI/CD на AWS

## AWS CDK

### Setup

```bash
# Install CDK
npm install -g aws-cdk

# New project
cdk init app --language typescript
# or
cdk init app --language python

# Bootstrap (once per account/region)
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### Basic Stack (TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export class MyStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB table
    const table = new dynamodb.Table(this, 'ItemsTable', {
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Lambda function
    const handler = new lambda.Function(this, 'ItemsHandler', {
      runtime: lambda.Runtime.NODEJS_18_X,
      code: lambda.Code.fromAsset('lambda'),
      handler: 'index.handler',
      environment: {
        TABLE_NAME: table.tableName,
      },
    });

    // Grant permissions
    table.grantReadWriteData(handler);

    // API Gateway
    const api = new apigateway.RestApi(this, 'ItemsApi', {
      restApiName: 'Items Service',
    });

    const items = api.root.addResource('items');
    items.addMethod('GET', new apigateway.LambdaIntegration(handler));
    items.addMethod('POST', new apigateway.LambdaIntegration(handler));
  }
}
```

### Python CDK

```python
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigateway,
    RemovalPolicy,
)
from constructs import Construct

class MyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # DynamoDB
        table = dynamodb.Table(
            self, "ItemsTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Lambda
        handler = lambda_.Function(
            self, "ItemsHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("lambda"),
            handler="index.handler",
            environment={
                "TABLE_NAME": table.table_name
            }
        )

        table.grant_read_write_data(handler)

        # API Gateway
        api = apigateway.RestApi(self, "ItemsApi")
        items = api.root.add_resource("items")
        items.add_method("GET", apigateway.LambdaIntegration(handler))
```

## Lambda Functions

### Python Lambda Template

```python
# lambda/index.py
import json
import os
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

def handler(event, context):
    http_method = event['httpMethod']
    path = event['path']

    try:
        if http_method == 'GET':
            if event.get('pathParameters'):
                # GET /items/{id}
                item_id = event['pathParameters']['id']
                response = table.get_item(Key={'id': item_id})
                item = response.get('Item')
                if not item:
                    return response_json(404, {'error': 'Not found'})
                return response_json(200, item)
            else:
                # GET /items
                response = table.scan()
                return response_json(200, response['Items'])

        elif http_method == 'POST':
            body = json.loads(event['body'])
            table.put_item(Item=body)
            return response_json(201, body)

        elif http_method == 'DELETE':
            item_id = event['pathParameters']['id']
            table.delete_item(Key={'id': item_id})
            return response_json(204, None)

    except Exception as e:
        return response_json(500, {'error': str(e)})

def response_json(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, cls=DecimalEncoder) if body else ''
    }
```

### Node.js Lambda Template

```javascript
// lambda/index.js
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, PutCommand, ScanCommand } = require('@aws-sdk/lib-dynamodb');

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);
const tableName = process.env.TABLE_NAME;

exports.handler = async (event) => {
  const { httpMethod, pathParameters, body } = event;

  try {
    switch (httpMethod) {
      case 'GET':
        if (pathParameters?.id) {
          const result = await docClient.send(new GetCommand({
            TableName: tableName,
            Key: { id: pathParameters.id }
          }));
          return response(200, result.Item);
        }
        const items = await docClient.send(new ScanCommand({ TableName: tableName }));
        return response(200, items.Items);

      case 'POST':
        const item = JSON.parse(body);
        await docClient.send(new PutCommand({
          TableName: tableName,
          Item: item
        }));
        return response(201, item);

      default:
        return response(400, { error: 'Unsupported method' });
    }
  } catch (error) {
    return response(500, { error: error.message });
  }
};

const response = (statusCode, body) => ({
  statusCode,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body)
});
```

## Common Patterns

### S3 Event Processing

```typescript
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';

const bucket = new s3.Bucket(this, 'UploadBucket');

const processor = new lambda.Function(this, 'Processor', {
  runtime: lambda.Runtime.PYTHON_3_11,
  code: lambda.Code.fromAsset('lambda'),
  handler: 'processor.handler',
});

bucket.addEventNotification(
  s3.EventType.OBJECT_CREATED,
  new s3n.LambdaDestination(processor),
  { suffix: '.json' }
);
```

### SQS Queue Processing

```typescript
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';

const queue = new sqs.Queue(this, 'TaskQueue', {
  visibilityTimeout: cdk.Duration.seconds(300),
});

const worker = new lambda.Function(this, 'Worker', {
  // ... config
});

worker.addEventSource(new lambdaEventSources.SqsEventSource(queue, {
  batchSize: 10,
}));
```

### Step Functions

```typescript
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';

const processTask = new tasks.LambdaInvoke(this, 'ProcessTask', {
  lambdaFunction: processLambda,
  outputPath: '$.Payload',
});

const notifyTask = new tasks.LambdaInvoke(this, 'NotifyTask', {
  lambdaFunction: notifyLambda,
});

const definition = processTask
  .next(new sfn.Choice(this, 'IsSuccess')
    .when(sfn.Condition.stringEquals('$.status', 'SUCCESS'), notifyTask)
    .otherwise(new sfn.Fail(this, 'Failed'))
  );

new sfn.StateMachine(this, 'StateMachine', {
  definition,
  timeout: cdk.Duration.minutes(5),
});
```

## CDK Commands

```bash
# Synthesize CloudFormation
cdk synth

# Diff changes
cdk diff

# Deploy
cdk deploy
cdk deploy --require-approval never  # CI/CD

# Deploy multiple stacks
cdk deploy Stack1 Stack2 --concurrency 2

# Destroy
cdk destroy

# List stacks
cdk ls

# Context
cdk context
cdk context --clear
```

## Best Practices

### Project Structure

```
my-cdk-app/
├── bin/
│   └── app.ts           # Entry point
├── lib/
│   ├── stacks/
│   │   ├── api-stack.ts
│   │   └── database-stack.ts
│   └── constructs/
│       └── api-lambda.ts
├── lambda/
│   ├── api/
│   └── workers/
├── test/
└── cdk.json
```

### Environment Separation

```typescript
// bin/app.ts
const app = new cdk.App();

new MyStack(app, 'MyStack-Dev', {
  env: { account: '111111111111', region: 'us-east-1' },
  stage: 'dev',
});

new MyStack(app, 'MyStack-Prod', {
  env: { account: '222222222222', region: 'us-east-1' },
  stage: 'prod',
});
```

### Tagging

```typescript
cdk.Tags.of(this).add('Project', 'MyProject');
cdk.Tags.of(this).add('Environment', props.stage);
cdk.Tags.of(this).add('Owner', 'team@example.com');
```

## Tips

1. **Use constructs** - переиспользуй паттерны
2. **Test locally** - SAM CLI для локального тестирования
3. **Environment variables** - храни конфиги в SSM/Secrets Manager
4. **Least privilege** - минимальные IAM permissions
5. **Cost awareness** - используй PAY_PER_REQUEST для DynamoDB
6. **Monitoring** - CloudWatch Logs + Alarms
7. **CI/CD** - автоматизируй деплой через CodePipeline
