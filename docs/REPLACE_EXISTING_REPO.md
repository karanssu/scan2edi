# Replace the existing GitHub repository safely

Do this only after you have downloaded/extracted the new Scan2EDI project.

## 1. Back up the current implementation

From the existing repository:

```bash
git status
git add -A
git commit -m "chore: checkpoint local OCR implementation"
git checkout -b backup/local-ocr-version
git push origin backup/local-ocr-version
git checkout main
```

## 2. Remove the old working tree but preserve Git history

**Linux / WSL / Git Bash:**

```bash
find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
```

Then copy every file from the new project into the repository root.

## 3. Commit the rewrite

```bash
git add -A
git commit -m "feat: rebuild Scan2EDI with cloud document extraction"
git push origin main
```

This keeps your repository URL and prior Git history while replacing the complete application codebase.
