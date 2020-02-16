from requests import Session, get
from hashlib import sha1
from datetime import datetime
from requests_toolbelt.adapters.host_header_ssl import HostHeaderSSLAdapter
import json, socket, os

def get_ipv4_address_for(site_url):
    addrs = socket.getaddrinfo(site_url, 443)
    ipv4_addrs = [addr[4][0] for addr in addrs if addr[0] == socket.AF_INET]
    return ipv4_addrs[0]

def simple_request(s, username, auth_token, domain, command, additional_data=None):
    
    data = {
        "user": username,
        "auth": auth_token,
        "command": command
        }

    data["data"] = {"domain": domain}

    if additional_data != None:
        data["data"].update(additional_data)

    single_wrapped_string_request = json.dumps({"request": data})
    double_wrapped_request = {"request": single_wrapped_string_request}

    wapi_ipv4_address = get_ipv4_address_for("api.wedos.com")

    response =  s.post(f"https://{wapi_ipv4_address}/wapi/json", data=double_wrapped_request)

    if response.json()["response"]["code"] != 1000:
        print("Stuff broke!")
        print(data)
        print(response.json()["response"]["result"])
        raise RuntimeError("wedos api does not like what this script does")
    else:
        print(f"{command} succeeded")

    return response

def change_row(s, username, auth_token, id, rdata, domain):
    
    additional_data = {
        "row_id": id,
        "ttl": 1800,
        "rdata": rdata
    }

    return simple_request(s, username, auth_token, domain, "dns-row-update", additional_data)

if os.path.exists("current_ip"):
    with open("current_ip", "r") as current_ip_file:
        current_ip_lines = current_ip_file.readlines()
        if current_ip_lines:
            current_ip = current_ip_lines[0]
        else:
            current_ip = "0.0.0.0"
else:
    current_ip = "0.0.0.0"

actual_ip = get("https://api.ipify.org").text

if actual_ip != current_ip:


    username = os.environ.get("WAPI_USERNAME")
    password = os.environ.get("WAPI_PASSWORD")
    domain = os.environ.get("WEDOS_DOMAIN")

    auththingy = sha1()
    auththingy.update(username.encode("ascii"))
    auththingy.update(sha1(password.encode("ascii")).hexdigest().encode("ascii"))
    auththingy.update(str(datetime.now().hour).encode("ascii"))

    auth_token = auththingy.hexdigest()


    s = Session()
    s.mount('https://', HostHeaderSSLAdapter())
    s.headers = {"host": "api.wedos.com"}

    response = simple_request(s, username, auth_token, domain, "dns-rows-list")

    rows = response.json()["response"]["data"]["row"]

    for row in rows:
        if row["name"] == "" and row["rdtype"] == "A":
            change_row(s, username, auth_token, row["ID"], actual_ip, domain)
        if row["name"] == "*" and row["rdtype"] == "A":
            change_row(s, username, auth_token, row["ID"], actual_ip, domain)

    simple_request(s, username, auth_token, domain, "dns-domain-commit", {"name": domain})
    
    with open("current_ip", "w") as current_ip_file:        
    	current_ip_file.write(actual_ip)

else:
    print("The ip is the same as the last time")
