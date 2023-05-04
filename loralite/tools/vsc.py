import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Convert cmd for vsc')
    parser.add_argument('cmd', help='Command', type=str)
    parser.add_argument('-r', help='Reverse', action='store_true')
    args = parser.parse_args()

    cmd: str = args.cmd
    pattern = 'python3 -m loralite.simulator.simulator '
    if not args.r:
        cmd = cmd.replace(pattern, '')
        # configs/config.json -c -u -d -n 1 -sbs -qof -cdppm 5 -gto -st 18400
        cmd = cmd.replace(' ', '", "')
        cmd = f'"{cmd}"'
        print(cmd)
    else:
        cmd = cmd.replace('"', '')
        cmd = cmd.replace(', ', ' ')
        print(f'{pattern}{cmd}')
        # "configs/config_scenarios.json", "-td", "600", "-tni", "500", "-en", "10", "-unp", "1", "-st", "86400", "-sbs", "-gto", "-nt", "UNKNOWN", "-di", "1", "-ndm", "2", "-sstf", "-qonmc", "-etj", "-pen", "-sibbtp", "10", "-npe", "-scenario", "4"