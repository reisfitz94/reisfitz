import boto3
import json
import os
import re

def lambda_handler(event, context):
    # Extract S3 bucket and key from the event
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']
    
    # Assume results are stored in a 'results' folder in the same bucket
    # Replace the file extension with .json for output
    base_key = os.path.splitext(key)[0]
    results_key = f'results/{base_key}.json'
    
    # Initialize Textract client
    textract = boto3.client('textract')
    
    # Analyze the document for text extraction
    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['FORMS']  # Use FORMS to help with structured data
    )
    
    # Extract text and confidences
    lines = []
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            lines.append({
                'text': block['Text'],
                'confidence': block['Confidence']
            })
    
    # Initialize variables
    payee_name = None
    payee_address = None
    confidence_name = 0.0
    confidence_address = 0.0
    fraudulent = False

    # combine all text for general scans
    full_text = ' '.join([line['text'] for line in lines])
    # flag any check that contains the word "fraudulent" anywhere
    if 'fraudulent' in full_text.lower():
        fraudulent = True

    # Helper predicates
    def contains_financial_terms(text):
        lower = text.lower()
        financial_terms = (
            'dollar',
            'usd',
            'amount',
            'amt',
            'memo',
            'pay to the order of'
        )
        return '$' in text or any(term in lower for term in financial_terms)

    def is_valid_name(text):
        # Names should not include numbers or financial terms.
        if contains_financial_terms(text):
            return False
        if re.search(r"\d", text):
            return False
        if len(text.split()) < 2:
            return False
        return True

    def looks_like_address(text):
        # require a number and at least one comma (street, city/country)
        if not re.search(r"\d", text):
            return False
        if ',' not in text:
            return False
        # simple length check to avoid short strings
        if len(text.split()) < 3:
            return False
        return True

    def is_valid_address(text):
        # Addresses may contain numbers (street number), but not currency/financial terms.
        if contains_financial_terms(text):
            return False
        return looks_like_address(text)

    # find center-most lines (bounding box center within [0.2,0.8] both axes)
    central_lines = []
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE' and 'Geometry' in block:
            bbox = block['Geometry']['BoundingBox']
            # center of the line
            center_x = bbox['Left'] + bbox['Width'] / 2
            center_y = bbox['Top'] + bbox['Height'] / 2
            if 0.2 <= center_x <= 0.8 and 0.2 <= center_y <= 0.8:
                central_lines.append({
                    'text': block.get('Text', '').strip(),
                    'confidence': block.get('Confidence', 0.0)
                })

    # candidate extraction from center lines
    name_candidates = []
    address_candidates = []
    for line in central_lines:
        txt = line['text']
        if not txt:
            continue
        if is_valid_address(txt):
            address_candidates.append(line)
        elif is_valid_name(txt):
            name_candidates.append(line)

    if name_candidates:
        best = max(name_candidates, key=lambda l: l['confidence'])
        payee_name = best['text']
        confidence_name = best['confidence'] / 100.0

    if address_candidates:
        best = max(address_candidates, key=lambda l: l['confidence'])
        payee_address = best['text']
        confidence_address = best['confidence'] / 100.0

    # if no address candidate we keep it null/0.0
    if not payee_address:
        payee_address = None
        confidence_address = 0.0

    # we do NOT enforce any confidence threshold here; both values are returned
    # even if they are low. The calling process can decide what to do with them.
    
    # Prepare the result JSON with explicit ordering and check name
    result = {
        'check_name': base_key,
        'payee_name': payee_name,
        'confidence_name': confidence_name,
        'payee_address': payee_address,
        'confidence_address': confidence_address,
        'fraudulent': fraudulent
    }
    
    # Upload the result to S3 under the results/ prefix (creates folder-like key)
    s3 = boto3.client('s3')
    # ensure the key uses unix style separators; results_key already does
    s3.put_object(
        Bucket=bucket,
        Key=results_key,
        Body=json.dumps(result, indent=2),
        ContentType='application/json'
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Check processed successfully')
    }