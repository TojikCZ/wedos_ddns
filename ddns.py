import ipaddress
from requests import Session, get
from hashlib import sha1
from datetime import datetime
from requests_toolbelt.adapters.host_header_ssl import HostHeaderSSLAdapter
import json, socket, os, sys

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

    #WAPI chce json v kolonce data 2x zabalený do {request: }
    single_wrapped_string_request = json.dumps({"request": data})
    double_wrapped_request = {"request": single_wrapped_string_request}

    wapi_ipv4_address = get_ipv4_address_for("api.wedos.com")

    response =  s.post(f"https://{wapi_ipv4_address}/wapi/json", data=double_wrapped_request)

    #Koukám jestli vše prošlo, padám pokud ne.
    if response.json()["response"]["code"] != 1000:
        print("Je to rozbitý!")
        print(data)
        print(response.json()["response"]["result"])
        raise RuntimeError("Wedos API se něco nelíbí")
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

# Změnila se nám odnaposled IP adresa?
if os.path.exists("current_ip"):
    with open("current_ip", "r") as current_ip_file:
        current_ip_lines = current_ip_file.readlines()
        if current_ip_lines:
            current_ip = current_ip_lines[0]
        else:
            current_ip = "0.0.0.0"
else:
    current_ip = "0.0.0.0"

global_ip_resp = get("https://api.ipify.org")
# Did we got even a 200?
if global_ip_resp.status_code != 200:
    print("Non 200 response during global ip retrieval with status {} and text {}.".format(global_ip_resp.status_code, global_ip_resp.text))
    sys.exit(1)
actual_ip = global_ip_resp.text
# Did they send something reasonable back?
try:
    addr = ipaddress.ip_address(actual_ip)
    # It should be a global one, otherwise it has no reason to exist in the global DNS data.
    if not addr.is_global:
        print("The address {} is not a global one.".format(addr))
        sys.exit(2)
except ValueError:
    print("The returned data {} do not comprise an IPV4 address.".format(actual_ip))
    sys.exit(3)


# Pokud se změnila ip, dohodni s WAPI změnu
if actual_ip != current_ip:

    # Seženu potřebné proměnné prostředí
    username = os.environ.get("WAPI_USERNAME")
    password = os.environ.get("WAPI_PASSWORD")
    domain = os.environ.get("WEDOS_DOMAIN")

    # poskládám autntizační token podle kuchařky od Wedosu
    auththingy = sha1()
    auththingy.update(username.encode("ascii"))
    auththingy.update(sha1(password.encode("ascii")).hexdigest().encode("ascii"))
    auththingy.update(str(datetime.now().hour).encode("ascii"))

    auth_token = auththingy.hexdigest()

    # Tvorba sezení pro requests s oním SSL adaptérem umožňujícím funkčnost SSL i při adresování pomocí IP
    s = Session()
    s.mount('https://', HostHeaderSSLAdapter())
    s.headers = {"host": "api.wedos.com"}

    response = simple_request(s, username, auth_token, domain, "dns-rows-list")

    rows = response.json()["response"]["data"]["row"]

    # Tady se prochází záznamy a kouká se který měnit
    # V if řádku je filtrování podle jména a typu záznamu
    # Pod tím se pak volá funkce co sestrojí požadavek pro úpravu. Zajímavá proměnná je actual_ip

    for row in rows:
        if row["name"] == "" and row["rdtype"] == "A":
            change_row(s, username, auth_token, row["ID"], actual_ip, domain)
        if row["name"] == "*" and row["rdtype"] == "A":
            change_row(s, username, auth_token, row["ID"], actual_ip, domain)

    # Nakonec požadavek o uložení změn.
    simple_request(s, username, auth_token, domain, "dns-domain-commit", {"name": domain})
    
    #Zapíšu si naši novou ip do souboru
    with open("current_ip", "w") as current_ip_file:        
    	current_ip_file.write(actual_ip)

else:
    print("The ip is the same as the last time")
