# enum_oblako

# Enum S3 buckets and SaaS

For now enum_oblako supports following services:
- Slack
- Atlassian
- Salesforce
- Yandex Gitlab
- Yandex Website
- Yandex Cloud S3
- VK Cloud S3
- Croc Cloud S3
- Selectel Cloud S3
- MTS Cloud S3
- Sbercloud S3
- Scaleway S3
- Exoscale S3
- OVHCloud S3
- Ionos S3
- Linode S3
- Vultr S3
- Digital Ocean S3

Enum_oblako can be run in two modes:
- Generate and enum (generate namespaces and bucketnames for you based on company's name)
- Enum (run enumeration based on submitted namespaces' and buckets' files)

# Install

```bash
python -m pip install enum_oblako
```

# Run

Generate:
```
enum_oblako --generate --name <name> --rps 100
```

Enum with prepared list (your namespaces and buckets files):
```
enum_oblako --namespaces namespaces.txt --buckets buckets.txt --name <test> --rps 100
```

Also it supports two regions: ru and eu (or all if you want both)
```
enum_oblako --generate --name <name> --region eu --rps 100
```
