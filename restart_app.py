import os
import sys
import subprocess
import time
import psutil


def kill_process_on_port(port=8100):
    """Kill any process running on the specified port."""
    for proc in psutil.process_iter(["pid", "name", "connections"]):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    print(
                        f"Found process {proc.info['name']} (PID: {proc.info['pid']}) using port {port}"
                    )
                    print(f"Terminating process...")
                    proc.terminate()
                    proc.wait(
                        5
                    )  # Wait for up to 5 seconds for the process to terminate
                    print(f"Process terminated.")
                    return True
        except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
            continue
    print(f"No process found using port {port}")
    return False


def restart_application():
    """Restart the FastAPI application."""
    print("Restarting application...")

    # Try to kill the process if it's running on the default port
    kill_process_on_port(8100)

    # Wait a moment for the port to be released
    time.sleep(2)

    # Start the application
    print("Starting application...")
    try:
        # Start the application in a non-blocking way using subprocess
        subprocess.Popen(
            [sys.executable, "main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        print("Application started successfully.")
        print("Please wait a few seconds for it to initialize completely.")
    except Exception as e:
        print(f"Error starting application: {str(e)}")


if __name__ == "__main__":
    # Check if psutil is installed
    try:
        import psutil
    except ImportError:
        print("The 'psutil' package is not installed. Installing it now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        print("psutil installed. Rerunning script...")
        # Restart the script to use the newly installed package
        os.execv(sys.executable, [sys.executable] + sys.argv)

    restart_application()
