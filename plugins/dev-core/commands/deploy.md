---
description: Universal deployment command для различных environments
argument-hint: [staging / production / local]
---

# 🚢 Deploy: $ARGUMENTS

Deploy to **$ARGUMENTS** environment

## Process:

### Pre-Deploy Checks
- [ ] Tests passing
- [ ] Linting clean
- [ ] No console.log / debugger
- [ ] Env variables configured
- [ ] Database migrations ready
- [ ] Backup created

### Deployment Steps
1. Build application
2. Run tests
3. Create Docker image (if applicable)
4. Push to registry
5. Deploy to environment
6. Run migrations
7. Health check
8. Smoke tests

### Post-Deploy
- Verify deployment
- Monitor logs
- Check metrics
- Notify team

**Environment-specific:**
- **local**: docker-compose up
- **staging**: Deploy to staging server, run E2E tests
- **production**: Blue-green deployment, gradual rollout

**Deploying! 🚢**