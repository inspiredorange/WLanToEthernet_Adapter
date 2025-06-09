# Test script to verify the environment check in main.py
print("Running environment compatibility test...")
try:
    import main
    print("ERROR: The script should have exited with an error message about MicroPython requirement.")
except SystemExit as e:
    print("SUCCESS: The script correctly detected non-MicroPython environment and exited.")
    print("Exit code:", e.code)
except Exception as e:
    print("UNEXPECTED ERROR:", type(e).__name__, "-", e)