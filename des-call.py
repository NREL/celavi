import argparse
from celavi.des import Context


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check CELAVI input data')
    parser.add_argument('--locations', help='Path to locations file')
    parser.add_argument('--step_costs', help='Path to step_costs file')
    parser.add_argument('--fac_edges', help='Facility edges file')
    parser.add_argument('--routes', help='Routes file')
    parser.add_argument('--transpo_edges', help='Transportation edges file')
    args = parser.parse_args()

    context = Context(
        locations_filename=args.locations,
        step_costs_filename=args.step_costs,
        possible_items=["nacelle", "blade", "tower", "foundation"]
    )
