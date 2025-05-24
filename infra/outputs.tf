output "cloudfront_domain" {
  value = aws_cloudfront_distribution.cdn.domain_name
}
output "api_gateway_id" {
  value = aws_api_gateway_rest_api.api.id
}
