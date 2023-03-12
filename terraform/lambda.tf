data "local_file" "source_code" {
  filename = "${path.module}/../flight_bot.zip"
}

provider "aws" {
  region = "ap-northeast-1"
  profile = "personal"
}

resource "aws_lambda_function" "terraform_lambda" {
  function_name = "MyFlightBot"

  filename = "../flight_bot.zip"
  source_code_hash = data.local_file.source_code.content_base64sha256

  handler = "lambda_function.lambda_handler"
  role    = "arn:aws:iam::925953579714:role/service-role/MyFlightBot-role-5jk4v7pv"  
  runtime  = "python3.9"
  timeout = 600

  layers = ["arn:aws:lambda:ap-northeast-1:925953579714:layer:requests_and_peewee:1"]
}
