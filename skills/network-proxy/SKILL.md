---
name: network-proxy
description: Rules for running network commands (curl, wget) from the terminal behind a proxy. Use whenever you are about to run curl, wget, or any command that downloads or calls a remote URL, or when such a command fails with a connection, name resolution, or SSL certificate error. Reads the proxy only from HTTP_PROXY and forbids any proxy use if it is not defined.
metadata:
  version: "1.1"
---

# Skill: network-proxy

Use the proxy defined in `$HTTP_PROXY`, and only that variable, for network
commands. If it is not defined, no proxy may be used.

## Prerequisites

Check whether the proxy is defined **without printing credentials**
(proxy URLs often contain `user:pass@`):

```bash
if [ -n "$HTTP_PROXY" ]; then
  echo "Proxy defined: $(printf '%s' "$HTTP_PROXY" | sed -E 's#//[^@/]*@#//***@#')"
else
  echo "No proxy defined"
fi
```

## Procedure

### If `HTTP_PROXY` is NOT defined (unset or empty)

- Run network commands directly.
- Do **not** add `-x`, `--proxy`, `use_proxy`, `http_proxy`, `https_proxy`,
  or any equivalent option.
- Do **not** invent, guess, or hardcode a proxy address.
- Do **not** disable certificate verification; on failure, report the
  original error.

### If `HTTP_PROXY` is defined

**1. First attempt: proxy with TLS verification enabled.**

```bash
curl -x "$HTTP_PROXY" --noproxy "${NO_PROXY:-}" "https://example.com/file"
```

```bash
wget -e use_proxy=on -e http_proxy="$HTTP_PROXY" -e https_proxy="$HTTP_PROXY" \
     -e no_proxy="${NO_PROXY:-}" "https://example.com/file"
```

If the user provides a corporate CA bundle, prefer it over disabling
verification: `curl --cacert /path/ca.pem ...` or
`wget --ca-certificate=/path/ca.pem ...`.

**2. Retry only on a certificate error** (`SSL certificate problem`,
`unable to get local issuer certificate`). Retry **once**, ignoring
verification, and tell the user that TLS verification was disabled for
that request:

```bash
curl -k -x "$HTTP_PROXY" --noproxy "${NO_PROXY:-}" "https://example.com/file"
```

```bash
wget --no-check-certificate -e use_proxy=on -e http_proxy="$HTTP_PROXY" \
     -e https_proxy="$HTTP_PROXY" -e no_proxy="${NO_PROXY:-}" "https://example.com/file"
```

For plain connection or name resolution errors, retrying with `-k` does not
help: report the error instead.

## Rules

- Read the proxy only from `$HTTP_PROXY`; no other variable.
- Never use `-k` / `--no-check-certificate` on requests that carry tokens,
  passwords, or other credentials (e.g. `Authorization` headers, Jira API
  calls). Report the error and ask the user.
- Never print the raw value of `HTTP_PROXY`.
- Hosts listed in `NO_PROXY` (internal services) must bypass the proxy.

## Output

Report the command outcome. If TLS verification was disabled, say so
explicitly.