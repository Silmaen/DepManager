from base64 import b64encode
from http.client import HTTPConnection


def basic_auth(username, password):
    token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def append_data_str(data: str, key: str, name: str, value: str):
    data += (
        f'--{key}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
    )
    return data


def main():
    url = "127.0.0.1"
    port = 8080
    user = "admin"
    passwd = "admin"

    conn = HTTPConnection(url, port)
    key = "###"
    headers = {
        "Authorization": basic_auth(user, passwd),
        "Content-Type": f"multipart/form-data;boundary={key}",
    }
    data = ""
    data = append_data_str(data, key, "action", "pull")
    data = append_data_str(data, key, "os", "w")
    data = append_data_str(data, key, "kind", "t")
    # end of data body
    data += f"--{key}--\r\n"
    conn.request("POST", "/api", body=data, headers=headers)
    resp = conn.getresponse()
    print(f"Code: {resp.status}, Reason: {resp.reason}")
    data = resp.read().decode("utf8").splitlines(keepends=False)
    print(f"DATA:")
    fp = open("response.html", "w")
    for line in data:
        print(f"{line}")
        fp.write(f"{line}\n")
    fp.close()
    print(f"END OF TRANSMISSION")


if __name__ == "__main__":
    main()
