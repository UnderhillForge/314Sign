import { initializeDatabase } from '../src/database';

// Setup test database before running tests
beforeAll(async () => {
  // Initialize database for tests
  initializeDatabase();
});

// Clean up after all tests
afterAll(async () => {
  // Close database connection if needed
  // The database will be cleaned up automatically
});
