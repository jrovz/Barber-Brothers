"""
Container debugging script for Barber Brothers application.

This script tests the Docker container locally before deploying to Cloud Run.
It helps identify issues with the container startup process.
"""
import os
import sys
import subprocess
import argparse
import time

def parse_args():
    parser = argparse.ArgumentParser(description='Debug Docker container for Barber Brothers application')
    parser.add_argument('--build-only', action='store_true', help='Only build the container, don\'t run it')
    parser.add_argument('--run-only', action='store_true', help='Only run the container, don\'t build it')
    parser.add_argument('--tag', default='barberia-app:debug', help='Docker image tag to use')
    parser.add_argument('--port', default='8080', help='Port to expose the container on')
    return parser.parse_args()

def run_command(command, shell=False, env=None):
    """Run a command and print its output in real-time"""
    print(f"Running: {command}")
    
    if isinstance(command, str) and not shell:
        command = command.split()
    
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=shell,
        env=env
    )
    
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
    
    process.wait()
    return process.returncode

def build_container(tag):
    """Build the Docker container"""
    print("\n=== Building Docker container ===")
    return run_command(f"docker build -t {tag} .")

def run_container(tag, port):
    """Run the Docker container locally with Cloud SQL emulation"""
    print("\n=== Running Docker container ===")
    
    # Create an environment similar to Cloud Run
    env = os.environ.copy()
    env.update({
        "PORT": port,
        "FLASK_ENV": "production",
        "FLASK_DEBUG": "1",
        "DB_ENGINE": "postgresql",
        "DB_NAME": "barberia-db",
        "DB_USER": "postgres",
        "DB_PASS": "y3WhoYFS",
        "GOOGLE_CLOUD_PROJECT": "barber-brothers-460514",
        "REGION": "us-central1",
        "INSTANCE_NAME": "barberia-db",
        "INSTANCE_CONNECTION_NAME": "barber-brothers-460514:us-central1:barberia-db"
    })
    
    # Remove any existing container with the same name
    run_command("docker rm -f barberia-debug-container", shell=True)
    
    # Run the container with Cloud SQL emulation
    cmd = f"""
    docker run --name barberia-debug-container -p {port}:{port} \
      -e PORT={port} \
      -e FLASK_ENV=production \
      -e FLASK_DEBUG=1 \
      -e DB_ENGINE=postgresql \
      -e DB_NAME=barberia-db \
      -e DB_USER=postgres \
      -e DB_PASS=y3WhoYFS \
      -e GOOGLE_CLOUD_PROJECT=barber-brothers-460514 \
      -e REGION=us-central1 \
      -e INSTANCE_NAME=barberia-db \
      -e INSTANCE_CONNECTION_NAME=barber-brothers-460514:us-central1:barberia-db \
      {tag}
    """
    return run_command(cmd, shell=True)

def main():
    args = parse_args()
    
    if not args.run_only:
        exit_code = build_container(args.tag)
        if exit_code != 0:
            print("\n❌ Container build failed")
            sys.exit(exit_code)
        print("\n✅ Container built successfully")
    
    if not args.build_only:
        exit_code = run_container(args.tag, args.port)
        if exit_code != 0:
            print("\n❌ Container run failed")
            sys.exit(exit_code)
        print("\n✅ Container ran successfully")

if __name__ == "__main__":
    main()
