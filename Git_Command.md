Create your first repository, then add and commit
files
At the command line, first verify that you have Git installed:
On all operating systems:
git --version
On UNIX-like operating systems:
GoalKicker.com – Git® Notes for Professionals 3
which git
If nothing is returned, or the command is not recognized, you may have to install Git on your system by
downloading and running the installer. See the Git homepage for exceptionally clear and easy installation
instructions.
After installing Git, configure your username and email address. Do this before making a commit.
Once Git is installed, navigate to the directory you want to place under version control and create an empty Git
repository:
git init
This creates a hidden folder, .git, which contains the plumbing needed for Git to work.
Next, check what files Git will add to your new repository; this step is worth special care:
git status
Review the resulting list of files; you can tell Git which of the files to place into version control (avoid adding files
with confidential information such as passwords, or files that just clutter the repo):
git add <file/directory name #1> <file/directory name #2> < ... >
If all files in the list should be shared with everyone who has access to the repository, a single command will add
everything in your current directory and its subdirectories:
git add .
This will "stage" all files to be added to version control, preparing them to be committed in your first commit.
For files that you want never under version control, create and populate a file named .gitignore before running
the add command.
Commit all the files that have been added, along with a commit message:
git commit -m "Initial commit"
This creates a new commit with the given message. A commit is like a save or snapshot of your entire project. You
can now push, or upload, it to a remote repository, and later you can jump back to it if necessary.
If you omit the -m parameter, your default editor will open and you can edit and save the commit message there.
Adding a remote
To add a new remote, use the git remote add command on the terminal, in the directory your repository is stored
at.
The git remote add command takes two arguments:
1. A remote name, for example, origin
2. A remote URL, for example, https://<your-git-service-address>/user/repo.git
 git remote add origin https://<your-git-service-address>/owner/repository.git
