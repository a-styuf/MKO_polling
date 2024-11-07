pyinstaller main.py --clean --onefile ^
                    --add-data="USB_TA_DRV.dll;." ^
                    --add-data="USB_TA_VC2.dll;." ^
                    --add-data="WDMTMKv2.dll;."
pause