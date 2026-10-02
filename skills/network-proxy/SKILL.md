---
name: network-proxy
description: Use when running network commands (curl, wget) in the terminal. Reads the proxy from the HTTP_PROXY environment variable, applies it to curl and wget, retries on network or SSL errors, and forbids any proxy use if HTTP_PROXY is not defined.
---

# Proxy Handling Instructions via Environment Variable

When running network commands (`curl`, `wget`, etc.) in the terminal, you must check and use the proxy address defined in the `$HTTP_PROXY` environment variable. No other variable is to be used.

### 1. Proxy Detection
Before building the command, read the value of the `$HTTP_PROXY` environment variable.

### 2. Format for `curl`
Use the environment variable directly within the command to pass the proxy and the flag to skip certificate verification:

```bash
curl -k -x "$HTTP_PROXY" "https://example.com/file"
```

### 3. Format for `wget`
Pass the environment variable to `wget`'s inline configuration:

```bash
wget --no-check-certificate -e use_proxy=on -e https_proxy="$HTTP_PROXY" "https://example.com/file"
```

### 4. Fallback / Retry Rule on Network or SSL Error
If a standard network command fails due to connection problems, name resolution issues, or SSL certificate errors (`SSL certificate problem`, `unable to get local issuer certificate`), you must retry the operation by injecting the proxy variable and ignoring SSL validation as shown in the examples above, **but only if `HTTP_PROXY` is defined (see section 5)**.

### 5. Mandatory Condition: Proxy Variable Must Be Declared
If `HTTP_PROXY` is not declared (unset or empty) in the environment:

- **No agent may use a proxy** for any network command.
- Do **not** add `-x`, `--proxy`, `use_proxy`, `https_proxy`, or any equivalent proxy option.
- Do **not** invent, guess, or hardcode a proxy address.
- Do **not** apply the fallback rule from section 4 (no retry with `-k` / `--no-check-certificate`); report the original error instead.

To check whether the proxy is defined, use:

```bash
if [ -n "$HTTP_PROXY" ]; then
  echo "Proxy defined: $HTTP_PROXY"
else
  echo "No proxy defined: run network commands directly, without proxy options."
fi
```