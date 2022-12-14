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

Enum_oblako can be run in two modes:
- Generate and enum (generate namespaces and bucketnames for you based on company's name)
- Enum (run enumeration based on submitted namespaces' and buckets' files)

Generate:
```
$ python3 enum_oblako.py --generate --name <name> --rps 100
```
Enum with prepared list (your namespaces and buckets files):
```
$ python3 enum_oblako.py --namespaces namespaces.txt --buckets buckets.txt --name <test> --rps 100
```
