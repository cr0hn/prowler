from prowler.lib.persistence import mklist
from prowler.lib.check.models import Check, Check_Report_AWS
from prowler.providers.aws.services.ec2.ec2_client import ec2_client
from prowler.providers.aws.services.ec2.lib.instance import get_instance_public_status
from prowler.providers.aws.services.ec2.lib.security_groups import check_security_group
from prowler.providers.aws.services.vpc.vpc_client import vpc_client


class ec2_instance_port_elasticsearch_kibana_exposed_to_internet(Check):
    # EC2 Instances with Elasticsearch/Kibana ports open to the Internet will be flagged as FAIL with a severity of medium if the instance has no public IP, high if the instance has a public IP but is in a private subnet, and critical if the instance has a public IP and is in a public subnet.
    def execute(self):
        findings = mklist()
        check_ports = [9200, 9300, 5601]
        for instance in ec2_client.instances:
            report = Check_Report_AWS(self.metadata())
            report.region = instance.region
            report.status = "PASS"
            report.status_extended = f"Instance {instance.id} does not have Elasticsearch/Kibana ports open to the Internet."
            report.resource_id = instance.id
            report.resource_arn = instance.arn
            report.resource_tags = instance.tags
            is_open_port = False
            if instance.security_groups:
                for sg in ec2_client.security_groups:
                    if sg.id in instance.security_groups:
                        for ingress_rule in sg.ingress_rules:
                            if check_security_group(
                                ingress_rule, "tcp", check_ports, any_address=True
                            ):
                                # The port is open, now check if the instance is in a public subnet with a public IP
                                report.status = "FAIL"
                                (
                                    report.status_extended,
                                    report.check_metadata.Severity,
                                ) = get_instance_public_status(
                                    vpc_client.vpc_subnets,
                                    instance,
                                    "Elasticsearch/Kibana",
                                )
                                is_open_port = True
                                break
                        if is_open_port:
                            break
            findings.append(report)
        return findings
