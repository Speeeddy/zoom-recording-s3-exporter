# zoom-recording-s3-exporter
An AWS set-up to automatically upload Zoom recordings to your S3 bucket for persistent storage, while recovering zoom recording storage limits.

This tool is beneficial for Zoom Pro users who need to store recording to a persistent storage like S3. Since this tool uses a Lambda function, the maximum size of file that can be processed is 500 MB (equal to /tmp storage provided by AWS Lambda). For files of greater size, modifications would be required to use ECS Fargate instead of a Lambda function.


# Installation instructions

## Setting up the CloudFormation stack
Use AWS SAM CLI to deploy this application. Clone this repository, and using SAM CLI from inside the cloned folder, execute:
`sam build` (Requires python3.7/pip)
`sam deploy --guided --capabilities CAPABILITY_NAMED_IAM` (Requires AWS credentials)
You may need to configure your AWS User credentials using `aws configure` prior to deploy step.

Other than this, you can also set this up directly using AWS CloudFormation by creating a stack. Note that the Lambda code may need to be inputted into `template.yaml` file (InlineCode) or set up separately.

## Setting up the zoom webhook

Refer to the [Zoom Recording Completed webhook](https://marketplace.zoom.us/docs/api-reference/webhook-reference/recording-events/recording-completed) and follow the instructions as given to set up the webhook. Your API Gateway endpoint which needs to be configured on Zoom Marketplace can be found in your CloudFormation stack -> Outputs OR using command `aws cloudformation describe-stacks --stack-name <name of your stack>` -> Stacks -> 0 -> Outputs -> OutputValue (where OutputKey is "ZoomRecordingCompleteWebhookUrl").


# CloudFormation template description
This template deploys resources needed for creating an API Gateway endpoint  to receive request from Zoom Recording Completed webhook, forward them to SQS  queue, and upload the files to S3 bucket using a lambda function. Files must be  less than 500MB in size.
  
## Parameters
The list of parameters for this template:

### ApiGatewayStageName 
Type: String 
Default: Release 
Description: Name of the stage of API Gateway. Affects the endpoint URL. 
### S3BucketName 
Type: String  
Description: Bucket name of S3 bucket to store recordings to. Bucket is created if "Create bucket" parameter is "true". Note that bucket name must be unique globally if creating a new bucket. 
### CreateNewS3Bucket 
Type: String  
Description: "true" if creating a new bucket, "false" if reusing an existing bucket. 

## Resources
The list of resources this template creates:

### ApiGatewayRestAPI 
Type: AWS::ApiGateway::RestApi
Creates an API Gateway endpoint which can be configured on Zoom to receive events whenever a new recording is available.  
### ApiGatewayResource 
Type: AWS::ApiGateway::Resource  
### ApiGatewayPostMethod 
Type: AWS::ApiGateway::Method  
### ApiGatewayOptionsCorsMethod 
Type: AWS::ApiGateway::Method  
### ApiGatewayDeployment 
Type: AWS::ApiGateway::Deployment  
### ZoomRecordingSqsFifo 
Type: AWS::SQS::Queue  
Queue to temporarily store requests and remove duplicates if any during the webhook call. Also allows lambda to run for greater than the API gateway timeout by decoupling them.
### ApiGatewayIntegrationSendMessageSqsRole 
Type: AWS::IAM::Role  
### S3BucketToCreate 
Type: AWS::S3::Bucket  
Conditional resource which creates bucket if "CreateNewS3Bucket" parameter is "true".
### StoreToS3LambdaSAM 
Type: AWS::Serverless::Function  
Lambda function which downloads the recording locally and uploads into S3.

## Outputs
The list of outputs this template exposes:

### ZoomRecordingCompleteWebhookUrl 
Description: API Gateway endpoint URL which will be called by Zoom whenever there is a new recording available. 

# Contributing
PRs are welcome.

## Future improvements
- Delete recording from Zoom to open up storage space automatically after successful upload.
- Error handling for failure scenarios (for eg. currently Zoom HTML page is downloaded if video link is incorrect).
- Notification using SNS/SES on status
- Deleting files from local /tmp directly in Lambda to make space for other files within the same recording
- Using ECS Fargate (serverless) for files larger than 500MB