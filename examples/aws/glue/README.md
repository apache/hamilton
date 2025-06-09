# Deploy Apache Hamilton Functions as an AWS Glue Job

[AWS Glue](https://aws.amazon.com/glue/) is a serverless data integration service. This guide demonstrates deploying a "hello-world" [processing job](https://docs.aws.amazon.com/glue/latest/dg/add-job-python.html) using Apache Hamilton functions on AWS Glue.

## Prerequisites

- **AWS CLI Setup**: Make sure the AWS CLI is set up on your machine. If you haven't done this yet, no worries! You can follow the [Quick Start guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html) for easy setup instructions.

## Step-by-Step Guide

### 1. Build wheel with Apache Hamilton functions

First things first, AWS Glue jobs run a single python script, but you can include external code (like our Apache Hamilton functions) by adding it as a python wheel. So, let's package our code and get it ready for action.

- **Install build package:**

    This command installs the 'build' package, which we'll use to create our python wheel.

    ```shell
    pip install build
    ```

- **Build python wheel:**

    ```shell
    cd app \
        && python -m build --wheel --skip-dependency-check \
        && cd ..
    ```

### 2. Upload all necessary files to S3

- **Upload the wheel file to S3:**

    Replace `<YOUR_PATH_TO_WHL>` with your specific S3 bucket and path:

    ```shell
    aws s3 cp \
        app/dist/hamilton_functions-0.1-py3-none-any.whl \
        s3://<YOUR_PATH_TO_WHL>/hamilton_functions-0.1-py3-none-any.whl
    ```

- **Upload main python script to s3:**

    Replace `<YOUR_PATH_TO_SCRIPT>` with your specific S3 bucket and path:

    ```shell
    aws s3 cp \
        processing.py \
        s3://<YOUR_PATH_TO_SCRIPT>/processing.py
    ```

- **Upload input data to s3:**

    Replace `<YOUR_PATH_TO_INPUT_DATA>` with your specific S3 bucket and path:

    ```shell
    aws s3 cp \
        data/input_table.csv \
        s3://<YOUR_PATH_TO_INPUT_DATA>
    ```

### 3. Create a simple role for AWS Glue job execution

- **Create the Role**:

    ```shell
    aws iam create-role \
        --role-name GlueProcessorRole \
        --assume-role-policy-document '{"Version": "2012-10-17", "Statement": [{ "Effect": "Allow", "Principal": { "Service": "glue.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
    ```

- **Attach Policies to the Role**:

    Here we grant full access to S3 as an example. For production environments it's important to restrict access appropriately.

    ```shell
    aws iam attach-role-policy \
        --role-name GlueProcessorRole \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    aws iam attach-role-policy \
        --role-name GlueProcessorRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole
    ```

### 4. Create and run the job

- **Create a job:**

    Ensure all paths are correctly replaced with the actual ones:

    ```shell
    aws glue create-job \
        --name test_hamilton_script \
        --role GlueProcessorRole \
        --command '{"Name" :  "pythonshell", "PythonVersion": "3.9", "ScriptLocation" : "s3://<YOUR_PATH_TO_SCRIPT>/processing.py"}' \
        --max-capacity 0.0625 \
        --default-arguments '{"--extra-py-files" : "s3://<YOUR_PATH_TO_WHL>/hamilton_functions-0.1-py3-none-any.whl", "--additional-python-modules" : "sf-hamilton"}'
    ```

- **Run the job:**

    Ensure all paths are correctly replaced with the actual ones:

    ```shell
    aws glue start-job-run \
        --job-name test_hamilton_script \
        --arguments '{"--input-table" : "s3://<YOUR_PATH_TO_INPUT_DATA>", "--output-table" : "s3://<YOUR_PATH_TO_OUTPUT_DATA>"}'
    ```

    Once you've run the job, you should see an output file at `s3://<YOUR_PATH_TO_OUTPUT_DATA>`.
