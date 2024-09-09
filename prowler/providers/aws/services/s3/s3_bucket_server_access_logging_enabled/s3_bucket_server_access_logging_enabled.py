from prowler.lib.check.models import Check, Check_Report_AWS
from prowler.lib.persistence import mklist
from prowler.providers.aws.services.s3.s3_client import s3_client


class s3_bucket_server_access_logging_enabled(Check):
    def execute(self):
        findings = mklist()
        for arn, bucket in s3_client.buckets.items():
            report = Check_Report_AWS(self.metadata())
            report.region = bucket.region
            report.resource_id = bucket.name
            report.resource_arn = arn
            report.resource_tags = bucket.tags
            if bucket.logging:
                report.status = "PASS"
                report.status_extended = (
                    f"S3 Bucket {bucket.name} has server access logging enabled."
                )
            else:
                report.status = "FAIL"
                report.status_extended = (
                    f"S3 Bucket {bucket.name} has server access logging disabled."
                )
            findings.append(report)

        return findings
