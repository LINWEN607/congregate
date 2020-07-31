# This is a shell of a script to run the docker fallback script across several container registry repositories
# Usage:
# - Uncomment the code below
# - Populate the repos array with tuples containing the source registry repo and destination registry repo
# - Kick off the script

# import subprocess

# repos = [
#     ("", "")
# ]

# for src, dest in repos:
#     command = "sudo -E ./manually_move_images.sh {0} {1}".format(src, dest)
#     subprocess.call(command.split(" "))
#     raw_input("\n{0} to {1} is complete. Would you like to proceed?".format(src, dest))