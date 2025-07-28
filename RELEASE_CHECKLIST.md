# Release Checklist

## Quick Release via GitHub Actions

1. Go to **Actions** → **📦 Release** workflow
2. Click **Run workflow**
3. Enter the new version (e.g., `0.15.1`)
4. Click **Run workflow**

✅ The workflow will automatically:

- Generate changelog using git-cliff
- Update version with Poetry
- Update README.md version references
- Commit all changes
- Open a Pull Request

## Pre-Release Checklist

- [ ] All tests passing on develop branch
- [ ] No outstanding critical issues
- [ ] Dependencies are up to date
- [ ] No pending PRs in the release milestone

## Post-Release Checklist

- [ ] Review the Pull Request created by the release workflow
- [ ] Merge the Pull Request
- [ ] Create a release tag
- [ ] Create a release note on GitHub
- [ ] Publish the release artifact to PyPI

## Manual Release Commands

If you need to release manually:

```bash
# Update version
poetry version 0.14.2
poetry lock --no-update

# Generate changelog
git cliff --tag v0.15.0 -o CHANGELOG.md

# Update README
sed -i 's/\[0\.[0-9]*\.[0-9]*\]/[0.14.2]/g' README.md

# Commit and tag
git add -A
git commit -m "chore(release): prepare for v0.15.1"
git tag -s v0.15.1 -m "Release v0.15.1"
git push origin v0.15.1
```
