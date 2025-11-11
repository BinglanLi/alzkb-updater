# Deployment Checklist

## Local Deployment

### Prerequisites
- [ ] Python 3.8 or higher installed
- [ ] pip package manager available
- [ ] Internet connection for API access

### Setup Steps
1. [ ] Clone or download the repository
2. [ ] Navigate to project directory: `cd AlzKB-updater-mcp`
3. [ ] Run the setup script:
   - Linux/Mac: `./run.sh`
   - Windows: `run.bat`
4. [ ] Verify output files in `data/processed/`

### First Run Verification
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Run with small limits for testing
cd src
python main.py --protein-limit 10 --compound-limit 10

# Verify outputs
ls -lh ../data/processed/
```

## GitHub Repository Deployment

### Initial Setup
1. [ ] Create new GitHub repository
2. [ ] Initialize git in project directory:
```bash
cd AlzKB-updater-mcp
git init
git add .
git commit -m "Initial commit: AlzKB updater"
```

3. [ ] Add remote and push:
```bash
git remote add origin https://github.com/YOUR_USERNAME/AlzKB-updater-mcp.git
git branch -M main
git push -u origin main
```

### GitHub Actions Setup
1. [ ] Go to repository Settings
2. [ ] Navigate to Actions → General
3. [ ] Under "Workflow permissions":
   - [ ] Select "Read and write permissions"
   - [ ] Check "Allow GitHub Actions to create and approve pull requests"
4. [ ] Save changes

### Verify GitHub Actions
1. [ ] Go to Actions tab
2. [ ] Click "Update AlzKB" workflow
3. [ ] Click "Run workflow" → "Run workflow"
4. [ ] Wait for completion (2-5 minutes)
5. [ ] Check for new CSV files in repository

### Schedule Configuration

Default schedule: Every Monday at 00:00 UTC

To change schedule, edit `.github/workflows/update-alzkb.yml`:

```yaml
on:
  schedule:
    # Examples:
    - cron: '0 0 * * 1'     # Every Monday at midnight
    - cron: '0 0 * * *'     # Every day at midnight
    - cron: '0 */6 * * *'   # Every 6 hours
    - cron: '0 0 1 * *'     # First day of every month
```

Cron format: `minute hour day month weekday`

## Production Deployment Considerations

### API Rate Limits
- [ ] Review rate limits for each data source
- [ ] Adjust `rate_limit` parameters if needed
- [ ] Consider implementing exponential backoff

### Data Volume
- [ ] Monitor repository size
- [ ] Consider archiving old CSV files
- [ ] Implement data retention policy

### Error Monitoring
- [ ] Check GitHub Actions logs regularly
- [ ] Set up email notifications for failures
- [ ] Review error logs in workflow outputs

### Data Validation
- [ ] Verify CSV file integrity
- [ ] Check record counts match expectations
- [ ] Validate data schema consistency

## Troubleshooting

### Common Issues

**Issue**: GitHub Actions workflow fails
- [ ] Check Actions logs for error messages
- [ ] Verify workflow permissions are set correctly
- [ ] Check if API endpoints are accessible

**Issue**: No data retrieved
- [ ] Verify internet connectivity
- [ ] Check if APIs are operational
- [ ] Review rate limiting settings
- [ ] Check query parameters

**Issue**: CSV files not committed
- [ ] Verify workflow permissions
- [ ] Check if there are actual changes to commit
- [ ] Review git configuration in workflow

**Issue**: Python dependencies fail
- [ ] Check requirements.txt is present
- [ ] Verify Python version compatibility
- [ ] Try running locally first

## Maintenance

### Regular Tasks
- [ ] Review logs weekly
- [ ] Check data quality monthly
- [ ] Update dependencies quarterly
- [ ] Archive old data as needed

### Updates
- [ ] Monitor API changes from data sources
- [ ] Update retrievers if APIs change
- [ ] Test thoroughly after updates
- [ ] Update documentation

### Backup
- [ ] GitHub automatically backs up code
- [ ] CSV files are version controlled
- [ ] Consider external backup for large datasets

## Security

### API Keys (if needed in future)
- [ ] Never commit API keys to repository
- [ ] Use GitHub Secrets for sensitive data
- [ ] Rotate keys regularly
- [ ] Use environment variables

### Access Control
- [ ] Review repository permissions
- [ ] Limit who can trigger workflows
- [ ] Monitor workflow execution logs

## Monitoring

### Success Metrics
- [ ] Data retrieval success rate
- [ ] Record count trends
- [ ] Workflow execution time
- [ ] API response times

### Alerts
Set up notifications for:
- [ ] Workflow failures
- [ ] Significant data volume changes
- [ ] API errors
- [ ] Unusual execution times

## Documentation

Keep updated:
- [ ] README.md with any changes
- [ ] CHANGELOG.md for version history
- [ ] API documentation references
- [ ] Deployment notes

## Support

If issues persist:
1. Check GitHub Actions logs
2. Review error messages in detail
3. Test locally with verbose logging
4. Verify API status pages
5. Review recent changes to codebase
