# moncontrol
**What this script can:**

Commands:  
usage: moncontrol.py [-h] [-m] [-s] [-c] [-p] [-d]

optional arguments:  
  ```-h, --help```            show this help message and exit  
  ```-m, --monitoring-connectivity```  
                        script will running permanently and check cabels connection. When condition of any cabel change, script will position monitors according to your previous settings.  
  ```-s, --set-monitors-positions-manually```  
                        in this mode u can position monitors (its position only in horizontal line now) much easier, comparing with xrandr  
  ```-c, --match-monitor-with-cable```  
                        this command will execute mode, that will help u understand, which monitor connected in specific port  
  ```-p, --show-saved-positions```  
                        show you all previously saved positions of monitors  
  ```-d, --delete-saved-config```  
                        delete certain previously saved configs  
 
**Setup:**
- install poetry (this is modern pip`s analog): https://python-poetry.org/docs/
- clone this repo to your directory
- go to this repos directory
- ```poetry install```
- Add to config of your shell variable:
moncontrol="cd /path_to_directory_that_consist_this_repo && poetry run python moncontrol.py"

If u want moncontrol works permanently, u can add moncontrol -m to your systemctl
