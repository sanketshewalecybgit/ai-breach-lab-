# Publish AI BreachLab on GitHub

Suggested repository name: **ai-breachlab**.

Suggested description: **Hands-on AI security labs by GhostStag Security. Eight evidence-driven challenges across Beginner, Intermediate, and Advanced tracks, with vulnerable and secure modes.**

Suggested topics: `ai-security`, `security-training`, `prompt-injection`, `llm-security`, `ctf`, `flask`, `educational`.

## Prepare a clean copy

From the project root:

```bash
python scripts/package_release.py
```

Extract `dist/ai-breachlab.zip` into a new folder. The extracted `ai-breachlab` directory includes dotfiles such as `.github` and `.gitignore`. It contains no local database or virtual environment. First launch creates fresh fictional seed data automatically.

The source archive is suitable for a repository upload or GitHub Release attachment. Merely uploading the ZIP as a repository file will not populate the source tree; extract it first.

## Publish with Git

Create an empty GitHub repository named `ai-breachlab`. Leave the automatic README, license, and gitignore options unchecked because these files are already provided. Then run the following from the extracted directory, replacing `YOUR-ACCOUNT` with the actual account or organization name:

```bash
git init -b main
git add .
git status --short
git commit -m "Initial release of AI BreachLab"
git remote add origin https://github.com/YOUR-ACCOUNT/ai-breachlab.git
git push -u origin main
```

Review the staged files before committing. Git will include `.github`, `.gitignore`, and `.gitattributes`. Authenticate using your normal GitHub Git setup. These instructions do not create a repository or publish anything until you run them.

For a browser upload, upload the extracted source files and directories, ensuring hidden files are included. Workflow files must end up in `.github/workflows/`, not inside an additional nested `ai-breachlab` directory.

## Repository settings

- Add the description and topics above.
- Confirm the MIT license and GhostStag Security credit are displayed.
- Enable Issues and private vulnerability reporting if available.
- Check the Actions tab after your first push. The test workflow covers Python 3.11, 3.12, and 3.13.
- After the first successful CI run, optionally create a release tag and attach the clean source ZIP.

CI is configured using the official [checkout action](https://github.com/actions/checkout) and [setup-python action](https://github.com/actions/setup-python), with read-only repository permissions and no deployment step.

## Run the lab

GitHub hosts the source, documentation, and release archive. The interactive application requires Python/Flask or Docker and runs on localhost. GitHub Pages does not execute this backend. Follow the README quick start after cloning or downloading.

The project's MIT license follows the [standard MIT license text](https://choosealicense.com/licenses/mit/). Bootstrap's separate license is preserved alongside the bundled stylesheet.
