# Deploy Apache Hamilton in AWS Lambda

[AWS Lambda](https://aws.amazon.com/lambda/) - serverless computation service in AWS.

Here we have an example how to deploy "hello-world" AWS Lambda with Apache Hamilton functions.
This example is based on the official instruction: https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions

## Prerequisites

- **AWS CLI Setup**: Make sure the AWS CLI is set up on your machine. If you haven't done this yet, no worries! You can follow the [Quick Start guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html) for easy setup instructions.

## Step-by-Step Guide

### 1. Build Docker image:

- **Build Docker image for deploy in AWS ECR**

  ```shell
  docker build --platform linux/amd64 -t aws-lambda-hamilton .
  ```

- **Local tests:**

  Run Docker container:

  ```shell
  docker run -p 9000:8080 aws-lambda-hamilton
  ```

  Send test request to check if Docker container executes it correctly:

  ```shell
  curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"body": {"columns":["signups","spend"],"index":[0,1,2,3,4,5],"data":[[1,10],[10,10],[50,20],[100,40],[200,40],[400,50]]}}'
  ```

### 2. Create AWS ECR repository:

Ensure the AWS account number (`111122223333`) is correctly replaced with yours:

- **Authenticate Docker to Amazon ECR**:

    Retrieve an authentication token to authenticate your Docker client to your Amazon Elastic Container Registry (ECR):

    ```shell
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 111122223333.dkr.ecr.us-east-1.amazonaws.com
    ```

- **Create the ECR Repository**:

    ```shell
    aws ecr create-repository --repository-name aws-lambda-hamilton \
        --region us-east-1 \
        --image-scanning-configuration scanOnPush=true \
        --image-tag-mutability MUTABLE
  ```

### 3. Deploy the Image to AWS ECR

Ensure the AWS account number (`111122223333`) is correctly replaced with yours:

```shell
docker tag aws-lambda-hamilton 111122223333.dkr.ecr.us-east-1.amazonaws.com/aws-lambda-hamilton:latest
docker push 111122223333.dkr.ecr.us-east-1.amazonaws.com/aws-lambda-hamilton:latest
```

### 4. Create a simple AWS Lambda role:

Example of creating an AWS Role for Lambda execution:

```shell
aws iam create-role \
    --role-name lambda-ex \
    --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
```

### 5. Create AWS Lambda

Ensure the AWS account number (`111122223333`) is correctly replaced with yours:

```shell
aws lambda create-function \
    --function-name aws-lambda-hamilton \
    --package-type Image \
    --code ImageUri=111122223333.dkr.ecr.us-east-1.amazonaws.com/aws-lambda-hamilton:latest \
    --role arn:aws:iam::111122223333:role/lambda-ex
```

### 6. Test AWS Lambda

```shell
aws lambda invoke \
    --function-name aws-lambda-hamilton \
    --cli-binary-format raw-in-base64-out \
    --payload '{"body": {"columns":["signups","spend"],"index":[0,1,2,3,4,5],"data":[[1,10],[10,10],[50,20],[100,40],[200,40],[400,50]]}}' \
    response.json
```
