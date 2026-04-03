# Claude Code Guidelines for Trobz Public Skills

## Documentation Maintenance

When making changes to this repository, **always consider updating the following files**:

### README.md Files

1. **Root `README.md`** - Update when:
   - Adding, removing, or renaming plugins
   - Changing command names or syntax
   - Modifying plugin features or capabilities
   - Updating installation instructions

2. **Plugin `README.md`** (e.g., `plugins/odoo/README.md`) - Update when:
   - Adding, removing, or renaming commands
   - Adding, removing, or renaming skills or agents
   - Changing command syntax or parameters
   - Modifying plugin behavior or features
   - Updating examples or quick start guides

### marketplace.json

Located at `.claude-plugin/marketplace.json`. Update when:

- Adding or removing plugins
- Changing plugin names, descriptions, or versions
- Updating plugin keywords or categories
- Modifying plugin metadata

## Command Namespace Convention

All commands in this marketplace use the `plugin-name:command` namespace format.

**Correct:** `/odoo:odooly`
**Incorrect:** `/odooly`

When adding or updating command examples anywhere in the repository, always use the full namespaced format.

## Consistency Checklist

Before completing any change, verify consistency across:

- [ ] Command definitions in `commands/*.md`
- [ ] Plugin README.md examples
- [ ] Root README.md examples and command tables
- [ ] marketplace.json metadata (if plugin-level changes)
- [ ] Run `pre-commit run --all-files` to validate hooks pass
