#!/usr/bin/env python3
"""
🦁 Animal Scraping Project Manager
Interactive CLI to manage Docker services, scraping, and data enrichment.
"""
import os
import sys
import subprocess
import time
import platform
import shutil

# Colors
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header():
    print(f"\n{BOLD}{CYAN}=== 🐾 Animal Scraping Manager ==={RESET}")
    print(f"{CYAN}OS: {platform.system()} | Python: {platform.python_version()}{RESET}\n")

def check_requirements():
    """Check if Docker is installed/running."""
    if not shutil.which("docker"):
        print(f"{RED}❌ Docker not found. Please install Docker Desktop.{RESET}")
        return False
    
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        print(f"{RED}⚠️  Docker daemon is not running. Please start Docker.{RESET}")
        return False

def run_command(command, description):
    """Run a shell command with user feedback."""
    print(f"{YELLOW}⏳ {description}...{RESET}")
    try:
        if platform.system() == "Windows":
            subprocess.run(command, shell=True, check=True)
        else:
            subprocess.run(command, shell=True, check=True, executable="/bin/bash")
        print(f"{GREEN}✓ Done.{RESET}")
        return True
    except subprocess.CalledProcessError:
        print(f"{RED}❌ Command failed.{RESET}")
        return False

def start_project():
    """Start the full stack via Docker Compose."""
    if not run_command("docker-compose up -d --build --remove-orphans", "Building and starting services"):
        return
    
    print(f"\n{GREEN}🚀 Services started!{RESET}")
    print(f"{BOLD}Waiting for Web App to be ready...{RESET}")
    
    # Wait for webapp
    retries = 30
    url = "http://localhost:8501"
    while retries > 0:
        try:
            import urllib.request
            if urllib.request.urlopen(url).getcode() == 200:
                print(f"{GREEN}✅ Web App is ready at {url}{RESET}")
                
                # Open browser
                try:
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", url])
                    elif platform.system() == "Windows":
                        os.startfile(url)
                    else:  # Linux
                        subprocess.run(["xdg-open", url])
                except:
                    pass
                return
        except:
            time.sleep(2)
            print(".", end="", flush=True)
            retries -= 1
    
    print(f"\n{RED}⚠️  Web App timed out, but container might still be starting.{RESET}")

def stop_project():
    """Stop all containers and clean up data volumes."""
    run_command("docker-compose down --remove-orphans -v", "Stopping services and cleaning data")

def run_enrichment():
    """Run the local python enrichment script."""
    print(f"\n{BOLD}🕷️  Running Enrichment Strategy:{RESET}")
    print("1. Fetch Wikipedia Description")
    print("2. Fetch Wikipedia Image")
    print("3. Fetch Wikidata Stats (Weight, Length, Lifespan)")
    print("4. Standardize Units (kg, cm, km/h)")
    
    # Check venv
    python_cmd = "python3"
    if os.path.exists("venv"):
        if platform.system() == "Windows":
            python_cmd = r"venv\Scripts\python"
        else:
            python_cmd = "venv/bin/python"
    
    cmd = f"{python_cmd} scripts/enrich_with_wikipedia.py"
    run_command(cmd, "Enriching Data")

def reload_database():
    """Force reload database from JSON."""
    print(f"\n{BOLD}💾 Reloading MongoDB & Elasticsearch...{RESET}")
    
    # Use localhost URIs for local script execution
    env_vars = (
        'export MONGODB_URI="mongodb://scraper:scraper_password@localhost:27017/animals_db?authSource=admin" && '
        'export ELASTICSEARCH_URL="http://localhost:9200" && '
    )
    
    python_cmd = "python3"
    if os.path.exists("venv"):
         if platform.system() != "Windows":
            python_cmd = "venv/bin/python"
            cmd = f"{env_vars} {python_cmd} scripts/load_data_on_startup.py"
         else:
            # Windows env vars syntax is different, simplifying for now or assumed run in git bash
            # For pure python cross-platform run, best to set os.environ inside python, 
            # or rely on the script being smart. But existing script reads os.environ.
            # Let's try passing vars via env argument if we were using subprocess.run(env=...), 
            # but here we use shell command string.
            print(f"{YELLOW}⚠️  On Windows, make sure you ran this from Git Bash or set env vars manually.{RESET}")
            cmd = f"venv\\Scripts\\python scripts/load_data_on_startup.py"
            
    else:
        cmd = f"{env_vars} python3 scripts/load_data_on_startup.py"

    run_command(cmd, "Loading Data")

def show_menu():
    while True:
        print_header()
        print(f"1. {GREEN}🚀 Start Project{RESET} (Docker Compose)")
        print(f"2. {RED}🛑 Stop Project{RESET}")
        print(f"3. {CYAN}✨ Enrich Data{RESET} (Local Script)")
        print(f"4. {YELLOW}💾 Reload Database{RESET} (Local Script)")
        print(f"5. {BOLD}🕷️  Run Scraper{RESET} (Re-crawl website)")
        print(f"6. 🚪 Exit")
        
        choice = input(f"\n{BOLD}Choose an option (1-6): {RESET}")
        
        if choice == "1":
            if check_requirements(): start_project()
        elif choice == "2":
            stop_project()
        elif choice == "3":
            run_enrichment()
        elif choice == "4":
            reload_database()
        elif choice == "5":
             run_command("docker-compose run --rm scrapy", "Running Scrapy Spider")
        elif choice == "6":
            print("Bye! 👋")
            sys.exit(0)
        else:
            print("Invalid choice, try again.")
        
        input(f"\n{CYAN}Press Enter to continue...{RESET}")

if __name__ == "__main__":
    try:
        show_menu()
    except KeyboardInterrupt:
        print("\nBye! 👋")
        sys.exit(0)
