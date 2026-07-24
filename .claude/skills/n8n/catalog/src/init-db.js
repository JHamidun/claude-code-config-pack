#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const WorkflowDatabase = require('./database');

async function initializeDatabase() {
  console.log('🔄 Initializing N8N Workflow Database...');
  
  try {
    // Ensure required directories exist
    await fs.ensureDir('database');
    await fs.ensureDir('workflows');
    await fs.ensureDir('static');
    
    console.log('✅ Directories created/verified');
    
    // Initialize database
    const db = new WorkflowDatabase();
    await db.initialize();
    
    // Get stats to verify database works
    const stats = await db.getStats();
    console.log('✅ Database initialized successfully');
    console.log(`📊 Current stats: ${stats.total} workflows`);
    
    db.close();
    
    console.log('\n🎉 Initialization complete!');
    console.log('Next steps:');
    console.log('1. Place your workflow JSON files in the "workflows" directory');
    console.log('2. Run "npm run index" to index your workflows');
    console.log('3. Run "npm start" to start the server');
    
  } catch (error) {
    console.error('❌ Initialization failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  initializeDatabase();
}

module.exports = { initializeDatabase }; 