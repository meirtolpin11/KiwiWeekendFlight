import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET_NAME = 'meirtolpin11-flightbot-bucket'


def download_from_bucket(key, local_path):
	global BUCKET_NAME

	s3 = boto3.resource('s3')
	try:
		logging.info(f"Downloading {key} From S3")
		local_path = '/tmp/'+key
		s3.Bucket(BUCKET_NAME).download_file(key, local_path)
		logging.info(f"{key} downloaded successfully to {local_path}")
	except Exception as e:
		logging.error(f"Error when Downloading {key} from S3: {e.message}")
	

def upload_to_bucket(path, key):
	logging.info(f"Uploading {path} to {key} in S3")
	try:
		s3 = boto3.resource('s3')
		s3.Bucket(BUCKET_NAME).upload_file(path, key)
		logging.info(f"{path} is successfully uploaded to S3")
	except Exception as e:
		logging.error(f"error while uploading {path} to S3: {e.message}")
