# Run Apache Hamilton Functions as an AWS SageMaker Processing Job

[AWS SageMaker](https://aws.amazon.com/sagemaker/) is a comprehensive platform that facilitates the creation, training, and deployment of machine learning (ML) models. This guide demonstrates deploying a "hello-world" [processing job](https://docs.aws.amazon.com/sagemaker/latest/dg/processing-job.html) using Apache Hamilton functions on SageMaker.

## Prerequisites

- **AWS CLI Setup**: Ensure that the AWS CLI is configured on your machine. Follow the [Quick Start guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html) for setup instructions.

## Step-by-Step Guide

### 1. Build the Docker Image

Navigate to the container directory and build the Docker image:

```shell
cd container/ \
    && docker build --platform linux/amd64 -t aws-sagemaker-hamilton . \
    && cd ..
```

### 2. Create AWS ECR repository.

Ensure the AWS account number (`111122223333`) is correctly replaced with yours:

- **Authenticate Docker to Amazon ECR**:

    Retrieve an authentication token to authenticate your Docker client to your Amazon Elastic Container Registry (ECR):

    ```shell
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 111122223333.dkr.ecr.us-east-1.amazonaws.com
    ```

- **Create the ECR Repository**:

    ```shell
    aws ecr create-repository \
        --repository-name aws-sagemaker-hamilton \
        --region us-east-1 \
        --image-scanning-configuration scanOnPush=true \
        --image-tag-mutability MUTABLE
    ```

### 3. Deploy the Image to AWS ECR

Ensure the AWS account number (`111122223333`) is correctly replaced with yours:

```shell
docker tag aws-sagemaker-hamilton 111122223333.dkr.ecr.us-east-1.amazonaws.com/aws-sagemaker-hamilton:latest
docker push 111122223333.dkr.ecr.us-east-1.amazonaws.com/aws-sagemaker-hamilton:latest
```

### 4. Create simple role for AWS SageMaker ScriptProcessor.

- **Create the Role**:

    Example of creating an AWS Role with full permissions for ECR and S3.

    ```shell
    aws iam create-role \
        --role-name SageMakerScriptProcessorRole \
        --assume-role-policy-document '{"Version": "2012-10-17", "Statement": [{ "Effect": "Allow", "Principal": { "Service": "sagemaker.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
    ```

- **Attach Policies to the Role**:

    Here we grant full access to ECR, S3 and SageMaker as an example. For production environments it's important to restrict access appropriately.

    ```shell
    aws iam attach-role-policy \
        --role-name SageMakerScriptProcessorRole \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    aws iam attach-role-policy \
        --role-name SageMakerScriptProcessorRole \
        --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess
    aws iam attach-role-policy \
        --role-name SageMakerScriptProcessorRole \
        --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
    ```

### 5. Install additional requirements

```shell
pip install -r requirements.txt
```

### 6. Execute the Processing Job

Find the detailed example in [notebook.ipynb](notebook.ipynb) to run the processing job.
