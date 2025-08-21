import os
import subprocess
import json
import re

def run_pylint_json(file_path, json_output_path):
    print("\n🔎 Running pylint...")
    try:
        # Run pylint with both JSON and text output
        result = subprocess.run(
            ["pylint", file_path, "-f", "json", "--output-format=json"],
            capture_output=True,
            text=True
        )

        # Save JSON output
        if result.stdout:
            with open(json_output_path, "w") as f:
                f.write(result.stdout)
            print(f"✅ Pylint JSON report saved to: {json_output_path}")
        else:
            print("⚠️ No pylint JSON output.")

        # Now rerun pylint to get score in text output
        score_result = subprocess.run(
            ["pylint", file_path],
            capture_output=True,
            text=True
        )

        match = re.search(r"Your code has been rated at ([\d\.]+)/10", score_result.stdout)
        if match:
            score = match.group(1)
            print(f"\n📊 Your pylint score: {score}/10")
        else:
            print("⚠️ Could not extract score.")

    except Exception as e:
        print(f"❌ Error running pylint: {e}")

def run_flake8(file_path):
    print("\n📏 Running flake8...")
    subprocess.call(["flake8", file_path])

def run_black(file_path):
    print("\n🎨 Running black (formatter)...")
    subprocess.call(["black", file_path])

def main():
    print("📋 Python Code Quality Checker with Score + Export")
    print("Type 'exit' or '8080' to quit.\n")

    while True:
        file_path = input("Enter Python file path to check: ").strip()
        if file_path.lower() in ['exit', 'quit', '8080']:
            print("👋 Exiting...")
            break

        if not os.path.isfile(file_path):
            print("❌ File not found. Please enter a valid Python file path.")
            continue

        json_output_path = file_path + "_pylint_report.json"

        run_pylint_json(file_path, json_output_path)
        run_flake8(file_path)

        choice = input("Do you want to auto-format this file using black? (y/n): ").strip().lower()
        if choice == 'y':
            run_black(file_path)

        print("\n✅ Check complete.\n")

if __name__ == "__main__":
    main()


'''HOW IT CALCULATE
🔍 How It Rates Code:
The app uses pylint to analyze the code based on:

PEP8 style violations (e.g., line too long)

Unused variables/imports

Bad naming or logic complexity

Missing docstrings and comments

The result is a rating out of 10 — for example: Your code has been rated at 7.85/10

You can optionally:

Export this score to a .json file

Log it for future comparison'''