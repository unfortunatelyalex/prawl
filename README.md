gold and exp farming timer script for brawlhalla patch 9.09 [(download)](https://github.com/phruut/prawl/releases/latest)\
please see the [wiki](https://github.com/phruut/prawl/wiki) for more information about the script\
help/dev server: https://discord.gg/2HDmuqqq9p  
video tutorial: https://youtu.be/SWuSntfHioQ
## 💡important
add this steam startup option
```
-noeac
```
> [!caution]
> please **always** use `-noeac` option before using the script to avoid the risk of any bans, although it is highly unlikely\
> _i am not responsible for anything that happens to your account_

## 🔥features
- launch brawlhalla from script (+auto launch on script start option)
- set custom values for script behavior timing adjustments
- auto start matches, also configurable
- show/hide brawlhalla window
- runs in the background (no interruption as it directly sends inputs to the brawlhalla window only)
- exp rate limit detection (starts again after waiting for the rate limit to reset)
- very light weight and minimal dependencies as it is basically just a timer script

### other
- [ ] pixel search mode
- [ ] fix input bugs(?)

## 🔎download
you can find the compiled script in the [releases page](https://github.com/phruut/prawl/releases), or [click here to download](https://github.com/phruut/prawl/releases/download/241209/farm_1209.exe)
> [!warning]
> your anti-virus may flag this executable as a threat, as it interacts with Win32 API for sending key inputs in the background

## 🚀manual install
> [!note]
> please use python 3.8 to 3.12 as DearPyGui 1.10.1 is not compatible with 3.13 and onwards
```bash
git clone https://github.com/https://github.com/phruut/prawl
```
```bash
cd prawl
```
```Pip Requirements
python -m pip install -r requirements.txt
```
and then you can run it
```bash
python farm.py
```

## compiled with nuitka
```bash
nuitka  --onefile --windows-console-mode=disable --windows-icon-from-ico=icon.ico farm.py
```
