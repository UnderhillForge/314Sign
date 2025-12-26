# Contributing to 314Sign

Help improve 314Sign! This guide covers development setup, coding standards, and contribution guidelines.

## Development Setup

### Prerequisites
- **Node.js 18+** (LTS recommended)
- **npm 8+**
- **Git**
- **VS Code** (recommended)

### Local Development
```bash
# Clone repository
git clone https://github.com/UnderhillForge/314Sign.git
cd 314Sign

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

### Development Workflow
1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally
3. Run tests: `npm test`
4. Commit changes: `git commit -m "Add my feature"`
5. Push branch: `git push origin feature/my-feature`
6. Create pull request

## Coding Standards

### TypeScript/JavaScript
- Use **TypeScript** for all new code
- Strict type checking enabled
- Use **ES6+** features (async/await, destructuring, etc.)
- Follow **ESLint** configuration
- Use **Prettier** for code formatting

### File Organization
```
src/
├── server.ts          # Main server file
├── database.ts        # Database connection and utilities
├── types/             # TypeScript type definitions
├── routes/            # API route handlers
├── middleware/        # Express middleware
├── utils/             # Utility functions
└── public/            # Static web assets
```

### Naming Conventions
- **Files**: kebab-case (e.g., `menu-control.ts`)
- **Classes**: PascalCase (e.g., `MenuController`)
- **Functions/Methods**: camelCase (e.g., `getMenuById()`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_PORT`)
- **Interfaces**: PascalCase with 'I' prefix (e.g., `IMenuData`)

### Database Schema
- Use **SQLite** with proper migrations
- Foreign key constraints enabled
- Indexed columns for performance
- Descriptive table/column names

## API Design Guidelines

### RESTful Endpoints
- Use proper HTTP methods (GET, POST, PUT, DELETE)
- Resource-based URLs: `/api/menus`, `/api/menus/:id`
- Consistent response formats
- Proper status codes (200, 201, 400, 404, 500)

### Error Handling
```typescript
// Good: Structured error responses
res.status(400).json({
  error: 'ValidationError',
  message: 'Menu name is required',
  details: { field: 'name' }
});

// Bad: Generic error responses
res.status(400).send('Error');
```

### Validation
- Input validation using middleware
- Sanitize user inputs
- Return detailed validation errors
- Type-safe request/response objects

## Testing

### Unit Tests
```bash
# Run all tests
npm test

# Run specific test file
npm test -- src/routes/menu.test.ts

# Watch mode for development
npm run test:watch
```

### Test Structure
- Tests in `__tests__/` directories
- Test files named `*.test.ts`
- Use Jest testing framework
- Mock external dependencies
- Test both success and error cases

### Code Coverage
- Aim for 80%+ code coverage
- Cover critical paths
- Test error conditions
- Include integration tests

## Pull Request Process

### Before Submitting
- [ ] Tests pass: `npm test`
- [ ] Code formatted: `npm run format`
- [ ] Linting passes: `npm run lint`
- [ ] Type checking: `npm run type-check`
- [ ] Documentation updated
- [ ] Commit messages follow conventions

### PR Description
```
## Summary
Brief description of changes

## Changes Made
- Feature: Added menu history tracking
- Fix: Resolved slideshow timing issue
- Docs: Updated API documentation

## Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual testing completed

## Breaking Changes
- None
- API endpoint renamed: /api/menus → /api/menu-items
```

### Review Process
1. Automated checks run (tests, linting, types)
2. Code review by maintainers
3. Approval and merge
4. Automatic deployment (if applicable)

## Documentation

### Code Documentation
- Use JSDoc comments for public APIs
- Document function parameters and return types
- Include usage examples where helpful
- Keep comments current with code changes

### User Documentation
- Update README.md for new features
- Add examples and screenshots
- Update troubleshooting guides
- Maintain API documentation

## Security

### Best Practices
- Input validation and sanitization
- SQL injection prevention (use parameterized queries)
- XSS protection (sanitize HTML output)
- CSRF protection for forms
- Secure default configurations

### Reporting Security Issues
- Email maintainers directly (don't create public issues)
- Include detailed reproduction steps
- Allow time for fixes before public disclosure

## Performance

### Frontend Optimization
- Minimize bundle size
- Lazy load components
- Optimize images and assets
- Use efficient CSS selectors
- Minimize DOM manipulations

### Backend Optimization
- Database query optimization
- Proper indexing
- Caching strategies
- Efficient algorithms
- Memory leak prevention

### Raspberry Pi Considerations
- Optimize for limited resources
- Minimize CPU usage
- Efficient file operations
- Proper error handling

## Deployment

### Production Builds
```bash
# Create production build
npm run build

# Start production server
npm start

# Or use PM2
pm2 start ecosystem.config.js
```

### Environment Variables
- Use `.env` files for configuration
- Don't commit secrets
- Document required environment variables
- Provide sensible defaults

## Issue Reporting

### Bug Reports
- Use issue templates
- Include reproduction steps
- Provide system information
- Attach relevant logs

### Feature Requests
- Describe the problem being solved
- Explain the proposed solution
- Consider alternative approaches
- Include mockups if applicable

## Community

### Getting Help
- GitHub Discussions for questions
- Stack Overflow with [314sign] tag
- Raspberry Pi forums for hardware-specific issues

### Communication
- Be respectful and constructive
- Use inclusive language
- Help newcomers learn
- Acknowledge contributions

## License

By contributing to 314Sign, you agree that your contributions will be licensed under the same license as the project (CC BY-NC 4.0).

---

Thank you for contributing to 314Sign! Your help makes digital signage better for everyone. 🎨📱
