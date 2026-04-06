# Check Processor for Amazon Lambda

This Python program is designed to process check images uploaded to Amazon S3 using AWS Lambda. It extracts the payee's name and address from the check image using Amazon Textract, and outputs the results as a JSON file in the 'results' folder of the same S3 bucket.

## Features

- Extracts payee name and address from check images
- Provides confidence scores for each extraction (no minimum threshold enforced in code)
- Flags checks marked as "fraudulent item"
- Outputs results in JSON format to S3

## Prerequisites

- AWS Lambda function with appropriate permissions
- Amazon S3 bucket for input and output
- Amazon Textract access
- Python 3.8+ runtime in Lambda

## Deployment

1. Package the `check_processor.py` file and `requirements.txt` into a ZIP file
2. Create a new Lambda function with Python runtime
3. Upload the ZIP file to Lambda
4. Set the handler to `check_processor.lambda_handler`
5. Configure S3 trigger for the input bucket
6. Ensure the Lambda role has permissions for S3 and Textract

## Input

- S3 event trigger when a check image is uploaded to the bucket

## Output

JSON file in the 'results' folder with the following structure:

```json
{
  "payee_name": "John Doe",
  "payee_address": "123 Main St, Anytown, USA",
  "confidence_name": 0.98,
  "confidence_address": 0.97,
  "fraudulent": false
}
```

If no valid address is found the field will be set to `null` and `confidence_address` will be 0.0; no confidence threshold is applied so both name and address scores are always returned.

## Notes

- Extraction looks only at text located in the **center region** of the check image; corner content is ignored.
- Extracted name or address must not contain numbers, dollar signs, or financial words (`dollar`, etc.) – those lines are filtered out.
- Addresses require a street number and at least one comma (street, city or country) to be considered valid; otherwise the address is `null`.
- Both payee name and address are returned independently, along with their confidence scores. There is **no** minimum confidence threshold in code; consumers of the JSON can decide how to interpret low scores.
- Fraud is flagged whenever the word “fraudulent” appears anywhere on the check. Name and address extraction still runs even for fraudulent checks.
- Only processes one check at a time as per Lambda event structure