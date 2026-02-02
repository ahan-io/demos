#!/usr/bin/python
class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OK = '\033[02m'        # Green
    WARNING = '\033[0;33m' # Yellow
    FAIL = '\033[0;31m'    # Red
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def main():
    print "\033[0;32mGREEN TEXT\033[0m"
    print Bcolors.FAIL + "Warning: No active frommets remain. Continue?" \
      + Bcolors.ENDC
    
if __name__ == '__main__':
    main()
