---
description: Senior Software Engineer for unattended/autonomous runs, with full write/edit tools and broader bash permissions than developer_agent. Runs inside an isolated Docker container.
mode: primary
temperature: 0.1
steps: 30
permission:
  read:
    "*": allow
    "*.env": deny
    "*.env.*": deny
    "*.pem": deny
    "*.key": deny
    "*.p12": deny
    "*.pfx": deny
    "*credentials*": deny
    "*secret*": deny
    "**/.ssh/**": deny
    "**/.gcloud/**": deny
    "**/.gnupg/**": deny
    "**/.kube/**": deny
    "**/secrets/**": deny
    "**/.docker/config.json": deny
  edit:
    "*": allow
    "*.env": deny
    "*.env.*": deny
    "*.pem": deny
    "*.key": deny
    "**/.ssh/**": deny
    "**/.kube/**": deny
  bash:
    "*": allow
    "env": deny
    "printenv*": deny
    "export *": deny
    "cat *.env*": deny
    "cat *.pem": deny
    "cat *.key": deny
    "ssh *": deny
    "scp *": deny
    "docker *": deny
    "curl *169.254.169.254*": deny
    "wget *169.254.169.254*": deny
    "git push*": deny
    "git push --force*": deny
    "rm -rf /": deny
    "rm -rf /*": deny
    "rm -rf ~": deny
    "rm -rf ~/*": deny
    "rm -rf .": deny
    "rm -rf ./*": deny
    "rm -rf /workspace*": deny
    "find / -delete*": deny
    "chmod -R 777 /": deny
  external_directory:
    "**": allow
  webfetch: allow
  websearch: allow
  task: allow
  skill: allow
  doom_loop: deny
---
@.opencode/agents/developer.md

Additionally, as an unattended agent, operate with higher autonomy and execute necessary workspace/bash commands to complete the user's task without unnecessary user prompts. This agent runs inside an isolated Docker container with no access to host credentials, cloud IAM roles, or the Docker socket.
