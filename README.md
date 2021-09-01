# moncontrol
**What this script can:**

Command:  
```python main.py --mode monitoring-connectivity```  
Description: script will run permanently and check cabels connection. When condition of any cabel will change, script will position monitors according to your previous settings.  

Command:  
```python main.py --mode set-monitors-positions-manually```  
Description: in this mode u can position monitors (its position only in horizontal line now) much easier, comparing with xrandr


Command:  
```python main.py match-monitor-with-cabel```  
Description: this command will execute mode, that will help u understand, which monitor connected in specific port

Command:  
```python main.py show-saved-positions```  
Description: show you previously saved positions of monitors

**Setup:**
- Clone this repo to your directory
- Go to this repos directory
- ```poetry install```
- Add to config of yout shell variable:
moncontrol="cd /path_to_directory_that_consist_this_repo/ | poetry run python moncontrol.py --mode"
