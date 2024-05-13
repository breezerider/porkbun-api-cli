import yaml


def compare_record_by_content_ttl_prio(target, other):
    """Compare a record from current configuration and an existing one returned by the API.
    Only consider record content, TTL and priority.

    :param domain_name: domain name
    :type domain_name: str
    :param target: target DNS record
    :type target: dict
    :param other: exisiting DNS record
    :type other: dict
    :returns: True if respective subfields are equal, False otherwise
    :rtype: bool"""
    return (
        target["content"] == other["content"]
        and ("ttl" not in target or target["ttl"] == other["ttl"])
        and ("prio" not in target or target["prio"] == other["prio"])
    )


def compare_record_by_name_type(domain_name, target, other):
    """Compare a record from current configuration and an existing one returned by the API.
    Only consider fqdn and record type.

    :param domain_name: domain name
    :type domain_name: str
    :param target: target DNS record
    :type target: dict
    :param other: exisiting DNS record
    :type other: dict
    :returns: True if respective subfields are equal, False otherwise
    :rtype: bool"""
    target_fqdn = f"{target['name']}.{domain_name}" if len(target["name"]) else domain_name
    return target_fqdn == other["name"] and target["type"] == other["type"]


def operation_allowed_by_mode(operation, mode):
    """Check whether an operation is allowed by current operation mode. Supported operations:

    * create
    * replace
    * update
    * upgrade

    :param operation: operation name
    :type operation: str
    :param mode: current operation mode
    :type mode: str
    :returns: True if operation is allowed, False otherwise
    :rtype: bool"""
    if mode == "append":
        return operation == "create"
    elif mode == "update":
        return operation == "update"
    elif mode == "upgrade":
        return operation in ["create", "update"]
    elif mode == "replace":
        return operation in ["create", "update", "delete"]
    return False


def load_config(config_file_path):
    """Load configuration from a YAML file with following format:

    :: code_block::yaml
       api:
         endpoint: str # API endpoint URI
         apikey: str # API key
         secretapikey: str # secret API key

       domains:
         - name: str
           records:
             - name: str # subdomain name, e.g., "", www, mail, etc
               type: enum[A, AAAA, CNAME, MX, NS, PTR, SRV, SOA, TXT, CAA, DS, DNSKEY]
               content: str # record value, e.g. IP address

    :param config_file_path: path to configuration file
    :type config_file_path: str
    :returns: dictionary with configuration
    :rtype: dict"""

    # Load the YAML configuration file
    with open(config_file_path, "r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if (
        config is None
        or any(x not in config for x in ["api", "domains"])
        or config["api"] is None
        or any(x not in config["api"] for x in ["apikey", "secretapikey"])
    ):
        raise ValueError("required objects 'api' and/or 'domain' with all required fields not found")

    if config["domains"] is None:
        config["domains"] = []

    return config
