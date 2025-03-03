import os
import json
import requests
from tqdm import tqdm
from argparse import ArgumentParser

API_VERSION = "v2"
BLOBS = []

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def fetch_repositories(url):
    response = requests.get(f"{url}/{API_VERSION}/_catalog", verify=False)
    response.raise_for_status()
    return response.json().get("repositories", [])

def fetch_tags(url, reponame):
    response = requests.get(f"{url}/{API_VERSION}/{reponame}/tags/list", verify=False)
    response.raise_for_status()
    return response.json().get("tags", [])

def fetch_manifest(url, reponame, tag):
    response = requests.get(f"{url}/{API_VERSION}/{reponame}/manifests/{tag}", verify=False)
    response.raise_for_status()
    return response.json()

def list_blobs(manifest_data):
    blobs = []
    if "fsLayers" in manifest_data:
        for layer in manifest_data["fsLayers"]:
            blob = layer['blobSum'].split(":")[1]
            if blob not in BLOBS:
                BLOBS.append(blob)
    return BLOBS

def download_blob(url, reponame, blob, dirname):
    file_path = os.path.join(dirname, f"{blob}.tar.gz")
    if os.path.exists(file_path):
        return
    response = requests.get(f"{url}/{API_VERSION}/{reponame}/blobs/sha256:{blob}", stream=True, verify=False)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    with open(file_path, 'wb') as file, tqdm(
        desc=f"Fetching {blob}",
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

def extract_tar_gz_files(dirname):
    print("\n[+] Unpacking all downloaded .tar.gz files...")
    for file in os.listdir(dirname):
        if file.endswith(".tar.gz"):
            file_path = os.path.join(dirname, file)
            os.system(f"tar -xvzf \"{file_path}\" -C \"{dirname}\" > /dev/null 2>&1")
    print("[+] All .tar.gz files have been unpacked successfully!")

def main():
    parser = ArgumentParser(description="Docker Registry Unauthenticated API Scanner")
    parser.add_argument('-u', '--url', required=True, help="URL Endpoint for Docker Registry API v2 (e.g., https://IP:Port)")
    args = parser.parse_args()
    url = args.url

    try:
        repos = fetch_repositories(url)
        print("\n[+] Available Repositories:\n")
        for repo in repos:
            print(repo)

        target_repo = input("\nWhich repository would you like to explore?: ").strip()
        if target_repo not in repos:
            print("The specified repository does not exist. Exiting....")
            return

        tags = fetch_tags(url, target_repo)
        if not tags:
            print("[+] No tags are available for this repository. Exiting....")
            return

        print("\n[+] Tags Found:\n")
        for tag in tags:
            print(tag)

        target_tag = input("\nWhich tag would you like to process?: ").strip()
        if target_tag not in tags:
            print("The specified tag does not exist. Exiting....")
            return

        manifest = fetch_manifest(url, target_repo, target_tag)
        blobs = list_blobs(manifest)

        dirname = input("\nEnter a directory name to store the artifacts: ").strip()
        os.makedirs(dirname, exist_ok=True)

        print(f"\n[+] Initiating download of blobs into the '{dirname}' directory...\n")

        for blob in blobs:
            download_blob(url, target_repo, blob, dirname)

        print("\n[+] All blobs have been successfully downloaded!")
        
        
        extract_tar_gz_files(dirname)

        print("\n[+] Process completed. Artifacts are ready for analysis.")

    except Exception as e:
        print(f"\n[-] An issue occurred: {e}")

if __name__ == "__main__":
    main()
