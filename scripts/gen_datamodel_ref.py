
import argparse
import json
import sys
from datamodel.products import SDSSDataModel

dm = SDSSDataModel()

#
# this script requires the datamodel to be installed
#

def generate_info(files: list[str], release: str) -> dict:
    data = {}
    for file in files:
        prod = dm.products[file]
        if release not in prod.releases:
            print(f"Product {prod} does not have a {release} release.")
            continue
        cols = prod.get_release(release).hdus['hdu1'].columns
        for key, c in cols.items():
            data[key] = c.model_dump()
    return data


def main():

    parser = argparse.ArgumentParser(description="Generate datamodel reference")
    parser.add_argument("-r",
        "--release",
        type=str,
        default="dr19",
        help="Release version to generate the datamodel for (default: dr19)",
    )
    parser.add_argument("-f", "--files",
                        type=str,
                        nargs='*',
                        help="Specific files to include in the datamodel generation")
    parser.add_argument('-o', '--output',
                        type=str,
                        default=None,
                        help="Output file for the datamodel")
    args = parser.parse_args()

    data = generate_info(args.files, args.release)

    output = args.output if args.output else f"{args.release.lower()}_dminfo.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f)

if __name__ == "__main__":
    main()
