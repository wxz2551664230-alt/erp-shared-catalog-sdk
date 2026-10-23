"""Read-only example. Set ERP_BASE_URL and ERP_USERNAME locally; password is prompted."""
import getpass
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from client import CatalogClient


def main():
    client = CatalogClient(os.environ["ERP_BASE_URL"])
    try:
        client.login(os.environ["ERP_USERNAME"], getpass.getpass("ERP password: "))
        page = client.search(search="", limit=10)
        for summary in page["items"]:
            print(summary["id"], summary["sku"], summary["name"])
        if page["items"]:
            detail = client.read(page["items"][0]["id"])
            print("Available variants:", len(detail["variants"]))
        print("Next cursor:", page["next_cursor"])
        # Explicit user-confirmed addition in your application:
        # receipt = client.add(validated_product)
        # Persist the original request and receipt['product_id'].
    finally:
        client.close()


if __name__ == "__main__":
    main()
