from json import dumps

from prowler.lib.check.models import Check, Check_Report_AWS
from prowler.lib.persistence import mklist
from prowler.lib.utils.utils import detect_secrets_scan
from prowler.providers.aws.services.ecs.ecs_client import ecs_client


class ecs_task_definitions_no_environment_secrets(Check):
    def execute(self):
        findings = mklist()
        secrets_ignore_patterns = ecs_client.audit_config.get(
            "secrets_ignore_patterns", []
        )
        for task_definition in ecs_client.task_definitions:
            report = Check_Report_AWS(self.metadata())
            report.region = task_definition.region
            report.resource_id = f"{task_definition.name}:{task_definition.revision}"
            report.resource_arn = task_definition.arn
            report.resource_tags = task_definition.tags
            report.status = "PASS"
            report.status_extended = f"No secrets found in variables of ECS task definition {task_definition.name} with revision {task_definition.revision}."
            if task_definition.environment_variables:
                dump_env_vars = {}
                for env_var in task_definition.environment_variables:
                    dump_env_vars.update({env_var.name: env_var.value})

                env_data = dumps(dump_env_vars, indent=2)
                detect_secrets_output = detect_secrets_scan(
                    data=env_data, excluded_secrets=secrets_ignore_patterns
                )
                if detect_secrets_output:
                    secrets_string = ", ".join(
                        [
                            f"{secret['type']} on line {secret['line_number']}"
                            for secret in detect_secrets_output
                        ]
                    )
                    report.status = "FAIL"
                    report.status_extended = f"Potential secret found in variables of ECS task definition {task_definition.name} with revision {task_definition.revision} -> {secrets_string}."

            findings.append(report)

        return findings
