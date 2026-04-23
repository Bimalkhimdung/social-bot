import os
import sys

def update_env_password(new_password):
    env_path = ".env"
    if not os.path.exists(env_path):
        print(f"Error: {env_path} file not found.")
        return

    with open(env_path, "r") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        # Check if the line starts with ADMIN_PASSWORD (handling potential spaces)
        if line.strip().startswith("ADMIN_PASSWORD="):
            new_lines.append(f"ADMIN_PASSWORD={new_password}\n")
            updated = True
        else:
            new_lines.append(line)

    # If the variable wasn't found at all, add it to the end
    if not updated:
        new_lines.append(f"ADMIN_PASSWORD={new_password}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)
    
    print(f"✅ Success! ADMIN_PASSWORD has been updated in {env_path}")
    print("⚠️  IMPORTANT: You must restart your backend server for the change to take effect.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python change_password.py <new_password>")
    else:
        new_pass = sys.argv[1]
        if not new_pass:
            print("Error: Password cannot be empty.")
        else:
            update_env_password(new_pass)
