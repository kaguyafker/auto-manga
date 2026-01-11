import py_compile
import os
import sys

files = [
    r"Database\database.py",
    r"Plugins\Post_Maker.py",
    r"Plugins\Settings\__init__.py",
    r"Plugins\Settings\admin_settings.py",
    r"Plugins\Settings\advanced_settings.py",
    r"Plugins\Settings\channel_settings.py",
    r"Plugins\Settings\file_settings.py",
    r"Plugins\Settings\input_helper.py",
    r"Plugins\Settings\main_settings.py",
    r"Plugins\Settings\media_settings.py",
    r"Plugins\Settings\monitor_settings.py",
    r"Plugins\Settings\settings_handler.py",
    r"Plugins\Sites\__init__.py",
    r"Plugins\Sites\allmanga.py",
    r"Plugins\Sites\mangadex.py",
    r"Plugins\Sites\mangaforest.py",
    r"Plugins\Sites\mangakakalot.py",
    r"Plugins\Sites\webcentral.py",
    r"Plugins\__init__.py",
    r"Plugins\admin.py",
    r"Plugins\downloading.py",
    r"Plugins\helper.py",
    r"Plugins\logs_dump.py",
    r"Plugins\search.py",
    r"Plugins\start.py",
    r"Plugins\uploading.py",
    r"Plugins\web_server.py",
    r"bot.py",
    r"config.py"
]

print("Starting Syntax Check...")
errors = 0
for f in files:
    if not os.path.exists(f):
        print(f"MISSING: {f}")
        errors += 1
        continue
        
    try:
        py_compile.compile(f, doraise=True)
        # print(f"OK: {f}")
    except py_compile.PyCompileError as e:
        print(f"FAIL: {f}")
        print(e.msg)
        errors += 1
    except Exception as e:
        print(f"ERROR: {f} - {e}")
        errors += 1

if errors == 0:
    print("SUCCESS: All files verified.")
    sys.exit(0)
else:
    print(f"FAILED: Found {errors} errors.")
    sys.exit(1)
